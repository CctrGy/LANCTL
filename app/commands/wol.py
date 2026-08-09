from __future__ import annotations

import argparse
import json
import math
import socket
import time
import uuid
from contextlib import suppress

from app.core.conditions import ConditionContext, duration, evaluate, parse_condition
from app.core.config import load_config
from app.core.credentials import CredentialStore
from app.core.database import DeviceDatabase
from app.core.file_transaction import locked_file
from app.core.history import DeviceSnapshot, HistoryEvent, HistoryService
from app.core.logger import write_log
from app.core.tasking import TASK_ID, JsonStore, result, utc_now
from app.models import Device
from app.plugins.wol_runtime import send_magic_packet, validate_mac
from app.protocols.ssh import SshProfile, run_remote_command
from app.services.element_scanner import ping_details
from app.services.lan_scanner import active_arp_mac

POWER_ACTIONS = {"shutdown", "restart", "sleep", "hibernate"}


def register_wol_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "wol", help="Enciende equipos mediante Wake-on-LAN y ejecuta secuencias seguras."
    )
    command.add_argument(
        "words",
        nargs="*",
        help="NAME [wakeup|status|shutdown|restart|sleep|hibernate|configure] o sequence ...",
    )
    command.add_argument(
        "-if", "--if", dest="conditions", action="append", default=[], metavar="CONDICIÓN"
    )
    command.add_argument("--if-all", action="append", default=[], metavar="CONDICIÓN")
    command.add_argument("--if-any", action="append", default=[], metavar="CONDICIÓN")
    command.add_argument("--if-not", action="append", default=[], metavar="CONDICIÓN")
    command.add_argument("-t", "--time", dest="schedule")
    command.add_argument("--message")
    command.add_argument("--force", action="store_true")
    command.add_argument("--cancel", action="store_true")
    command.add_argument("--broadcast", default=None)
    command.add_argument("--port", type=int, default=None)
    command.add_argument("--repeat", type=int, default=None)
    command.add_argument("--interval", type=float, default=None)
    command.add_argument("--wait", type=float, default=None)
    command.add_argument("--method", choices=("auto", "arp", "ping", "port"), default=None)
    command.add_argument("--check-port", type=int, default=None)
    command.add_argument("--interface")
    command.add_argument("--retry", type=int, default=0)
    command.add_argument("--dry-run", action="store_true")
    command.add_argument("--json", action="store_true")
    command.add_argument("--quiet", action="store_true")
    command.add_argument("--group")
    command.add_argument("--all", action="store_true")
    command.add_argument("--yes", action="store_true")
    command.add_argument("--after", action="append", default=[])
    command.add_argument("--delay")
    command.add_argument("--timeout", type=float, default=60)
    command.add_argument("--on-failure", choices=("stop", "continue", "retry"), default="stop")
    command.add_argument("--cooldown")
    command.add_argument("--max-attempts", type=int, default=1)
    command.add_argument("--power-transport", choices=("ssh", "disabled"))
    command.add_argument("--power-platform", choices=("windows", "linux"))
    command.add_argument("--power-command", action="append", default=[], metavar="ACCIÓN=COMANDO")
    command.add_argument("--database", default=config["database"])
    command.add_argument("--store", default=config["credentials"])
    command.add_argument(
        "--sequences", default=config.get("wolSequences", "data/lc/wol-sequences.json")
    )
    help_by_dest = {
        "conditions": "Condición AND adicional (repetible).",
        "if_all": "Condición AND adicional.",
        "if_any": "Condición OR adicional.",
        "if_not": "Condición negada.",
        "schedule": "Momento del apagado programado.",
        "message": "Mensaje remoto, si el transporte lo admite.",
        "force": "Solicita cierre forzado al transporte.",
        "cancel": "Cancela una programación, si el transporte lo admite.",
        "broadcast": "IPv4 de broadcast.",
        "port": "Puerto UDP WOL.",
        "repeat": "Número de paquetes mágicos.",
        "interval": "Intervalo entre paquetes.",
        "wait": "Segundos máximos de verificación.",
        "method": "Método de verificación.",
        "check_port": "Puerto TCP de comprobación.",
        "interface": "IPv4 local de salida.",
        "retry": "Reintentos completos.",
        "dry_run": "Valida sin enviar.",
        "json": "Salida JSON estructurada.",
        "quiet": "Omite salida humana.",
        "group": "Actúa sobre un grupo.",
        "all": "Actúa sobre todo el inventario.",
        "yes": "Confirma explícitamente --all.",
        "after": "Dependencia de paso.",
        "delay": "Espera previa del paso.",
        "timeout": "Timeout de paso.",
        "on_failure": "Política ante fallo.",
        "cooldown": "Espera mínima entre ejecuciones.",
        "max_attempts": "Máximo de intentos.",
        "power_transport": "Transporte autorizado para apagar o reiniciar.",
        "power_platform": "Sistema operativo remoto.",
        "power_command": "Plantilla administrada ACCIÓN=COMANDO.",
        "database": "Archivo JSON de elementos.",
        "store": "Almacén cifrado de credenciales.",
        "sequences": "Archivo transaccional de secuencias.",
    }
    for parser_action in command._actions:
        if parser_action.help is None:
            parser_action.help = help_by_dest.get(parser_action.dest, "Opción Wake-on-LAN.")
    command.set_defaults(handler=run_wol)


def _online(device, method: str, timeout: float, check_port: int | None) -> bool:
    if not device.ip or device.ip == "-":
        return False
    if method in {"auto", "arp"} and active_arp_mac(device.ip, min(timeout, 1.0)):
        return True
    if method in {"auto", "ping"} and ping_details(device.ip, min(timeout, 1.0))[0]:
        return True
    if method == "port":
        if check_port is None:
            raise ValueError("--method port requiere --check-port")
        try:
            with socket.create_connection((device.ip, check_port), timeout=min(timeout, 1.0)):
                return True
        except OSError:
            return False
    return False


def _options(args, device, defaults=None) -> dict:
    if defaults is None:
        configured = load_config().get("wol", {})
        defaults = configured if isinstance(configured, dict) else {}
    local = device.protocol_options.get("wol", {})
    values = {
        "broadcast": "255.255.255.255",
        "port": 9,
        "repeat": 3,
        "interval": 0.5,
        "wait": 60,
        "method": "auto",
    }
    values.update(defaults)
    values.update(local)
    for arg, key in (
        (args.broadcast, "broadcast"),
        (args.port, "port"),
        (args.repeat, "repeat"),
        (args.interval, "interval"),
        (args.wait, "wait"),
        (args.method, "method"),
    ):
        if arg is not None:
            values[key] = arg
    if not 0 <= float(values["wait"]) <= 3600:
        raise ValueError("wait debe estar entre 0 y 3600 segundos")
    if not 0 <= args.retry <= 10:
        raise ValueError("retry debe estar entre 0 y 10")
    if args.check_port is not None and not 1 <= args.check_port <= 65535:
        raise ValueError("check-port fuera de 1..65535")
    return values


def _condition_passes(args, device, database, method, timeout, inventory=None) -> bool:
    def online(selector):
        return _online(
            database.resolve(selector, devices=inventory), method, timeout, args.check_port
        )

    context = ConditionContext(
        online=online,
        target=device.device_id,
        last_seen=device.last_seen,
        group_members=lambda name: [
            d.device_id
            for d in (inventory if inventory is not None else database.load())
            if d.in_group(name)
        ],
    )
    all_conditions = [parse_condition(x) for x in args.conditions + args.if_all]
    any_conditions = [parse_condition(x) for x in args.if_any]
    not_conditions = [parse_condition(x) for x in args.if_not]
    return (
        all(evaluate(x, context) for x in all_conditions)
        and (not any_conditions or any(evaluate(x, context) for x in any_conditions))
        and not any(evaluate(x, context) for x in not_conditions)
    )


def _wake(
    args, database, selector: str | Device, *, task_id="wol.wakeup", inventory=None, defaults=None
) -> dict:
    started = utc_now()
    run_id = str(uuid.uuid4())
    target = selector.device_id if isinstance(selector, Device) else selector
    try:
        device = selector if isinstance(selector, Device) else database.resolve(selector)
    except ValueError as error:
        return result(
            task_id,
            "wol.resolve.device",
            target,
            "error",
            started,
            code="WOL.RESOLVE.DEVICE",
            message=str(error),
            run_id=run_id,
        ).to_dict()
    try:
        validate_mac(device.mac)
    except ValueError as error:
        return result(
            task_id,
            "wol.resolve.mac",
            target,
            "invalid",
            started,
            code="WOL.MAC.INVALID",
            message=str(error),
            run_id=run_id,
        ).to_dict()
    options = _options(args, device, defaults)
    method = str(options["method"])
    if not _condition_passes(
        args, device, database, method, min(float(options["wait"]), 1), inventory
    ):
        return result(
            task_id,
            "wol.condition.evaluate",
            target,
            "skipped",
            started,
            detail={"reason": "condition-false"},
            run_id=run_id,
        ).to_dict()
    already = _online(device, method, 1, args.check_port)
    if args.dry_run:
        status = "online" if already else "sent"
        return result(
            task_id,
            "wol.wakeup.prepare",
            target,
            status,
            started,
            detail={**options, "dryRun": True, "mac": device.mac},
            run_id=run_id,
        ).to_dict()
    try:
        for attempt in range(args.retry + 1):
            send_magic_packet(
                device.mac,
                options["broadcast"],
                options["port"],
                options["repeat"],
                options["interval"],
                args.interface,
            )
            _write_wol_history(
                device,
                "wol.wakeup.sent",
                "sent",
                run_id,
                task_id,
                "wol.wakeup.send",
                "Paquete Wake-on-LAN enviado",
            )
            if already or not options["wait"]:
                break
            deadline = time.monotonic() + float(options["wait"])
            while time.monotonic() < deadline:
                if _online(device, method, 1, args.check_port):
                    return result(
                        task_id,
                        "wol.wakeup.verify",
                        target,
                        "online",
                        started,
                        detail={"attempt": attempt + 1, "sent": True},
                        run_id=run_id,
                    ).to_dict()
                time.sleep(min(1, max(0, deadline - time.monotonic())))
        if already:
            return result(
                task_id,
                "wol.wakeup.verify",
                target,
                "online",
                started,
                detail={"alreadyOnline": True, "sent": True},
                run_id=run_id,
            ).to_dict()
        if not options["wait"]:
            return result(
                task_id,
                "wol.wakeup.send",
                target,
                "sent",
                started,
                detail={"confirmed": False},
                run_id=run_id,
            ).to_dict()
        return result(
            task_id,
            "wol.wakeup.verify",
            target,
            "timeout",
            started,
            code="WOL.VERIFY.TIMEOUT",
            message="El dispositivo no fue detectado; el paquete enviado no garantiza el encendido",
            run_id=run_id,
        ).to_dict()
    except Exception as error:  # noqa: BLE001 - frontera de adaptadores de red
        return result(
            task_id,
            "wol.wakeup.send",
            target,
            "error",
            started,
            code="WOL.SEND.ERROR",
            message=str(error),
            run_id=run_id,
        ).to_dict()


def _sequence(args, database) -> dict | list:
    store = JsonStore(args.sequences)
    configured = load_config().get("wol", {})
    defaults = configured if isinstance(configured, dict) else {}
    with locked_file(store.path):
        return _sequence_locked(args, database, store, defaults)


def _sequence_locked(args, database, store, defaults=None) -> dict | list:
    if len(args.words) < 2:
        raise ValueError("usa wol sequence create ID o wol sequence ID run")
    data = store.load()
    words = args.words[1:]
    if words[0] == "create":
        if len(words) != 2 or not TASK_ID.fullmatch(words[1]):
            raise ValueError("id de secuencia no válido")
        if words[1] in data["sequences"]:
            raise ValueError("la secuencia ya existe")
        data["sequences"][words[1]] = {
            "id": words[1],
            "steps": [],
            "cooldown": args.cooldown,
            "maxAttempts": args.max_attempts,
        }
        store.save(data)
        return {"status": "success", "sequence": words[1]}
    sequence_id = words[0]
    if sequence_id not in data["sequences"]:
        raise ValueError("secuencia no encontrada")
    sequence = data["sequences"][sequence_id]
    action = words[1] if len(words) > 1 else "run"
    if action == "add":
        if len(words) < 3:
            raise ValueError("falta el objetivo del paso")
        target = words[2]
        step_id = target.casefold().replace(" ", "-")
        step = {
            "id": step_id,
            "action": "wakeup",
            "target": target,
            "requires": [x.casefold().replace(" ", "-") for x in args.after],
            "delay": args.delay,
            "wait": "online",
            "timeout": args.timeout,
            "retry": args.retry,
            "onFailure": args.on_failure,
        }
        if any(x["id"] == step_id for x in sequence["steps"]):
            raise ValueError("el paso ya existe")
        sequence["steps"].append(step)
        _validate_graph(sequence["steps"])
        store.save(data)
        return {"status": "success", "sequence": sequence_id, "step": step}
    if action != "run":
        raise ValueError("acción de secuencia no soportada")
    _validate_graph(sequence["steps"])
    states = {}
    results = []
    pending = list(sequence["steps"])
    while pending:
        progressed = False
        for step in list(pending):
            if any(dep not in states for dep in step["requires"]):
                continue
            pending.remove(step)
            progressed = True
            failed = next(
                (
                    dep
                    for dep in step["requires"]
                    if states[dep] not in {"success", "online", "sent", "skipped"}
                ),
                None,
            )
            if failed:
                row = result(
                    f"sequence.{sequence_id}.{step['id']}",
                    "wol.sequence.dependency",
                    step["target"],
                    "blocked",
                    utc_now(),
                    code="WOL.SEQUENCE.BLOCKED",
                    message="Dependencia no completada",
                    dependency=failed,
                ).to_dict()
            else:
                if step.get("delay"):
                    time.sleep(duration(step["delay"]))
                row = _wake(
                    args,
                    database,
                    step["target"],
                    task_id=f"sequence.{sequence_id}.{step['id']}",
                    defaults=defaults,
                )
            states[step["id"]] = row["status"]
            results.append(row)
        if not progressed:
            raise ValueError("dependencias de secuencia irresolubles")
    data["runs"][results[0]["runId"] if results else str(uuid.uuid4())] = {
        "sequence": sequence_id,
        "results": results,
    }
    store.save(data)
    return results


def _validate_graph(steps: list[dict]) -> None:
    ids = {x["id"] for x in steps}
    if any(dep not in ids for step in steps for dep in step.get("requires", [])):
        raise ValueError("dependencia de secuencia inexistente")
    visiting = set()
    done = set()
    mapping = {x["id"]: x.get("requires", []) for x in steps}

    def visit(node):
        if node in visiting:
            raise ValueError("la secuencia contiene un ciclo")
        if node in done:
            return
        visiting.add(node)
        for dep in mapping[node]:
            visit(dep)
        visiting.remove(node)
        done.add(node)

    for node in mapping:
        visit(node)


def _configure_power(args, database, selector: str) -> dict:
    device = database.resolve(selector)
    options = dict(device.protocol_options.get("wol", {}))
    if args.power_transport is not None:
        options["powerTransport"] = args.power_transport
    if args.power_platform is not None:
        options["powerPlatform"] = args.power_platform
    commands = dict(options.get("powerCommands", {}))
    for definition in args.power_command:
        action, separator, command = definition.partition("=")
        action = action.strip().casefold()
        if not separator or action not in POWER_ACTIONS or not command.strip():
            raise ValueError("--power-command debe usar ACCIÓN=COMANDO")
        commands[action] = command.strip()
    if commands:
        options["powerCommands"] = commands
    if options.get("powerTransport") == "ssh":
        if options.get("powerPlatform") not in {"windows", "linux"}:
            raise ValueError("el transporte SSH requiere --power-platform")
        if "ssh" not in device.protocols or not device.credentials.get("ssh"):
            raise ValueError("configura SSH y su credencial antes del transporte de energía")
    updated = database.configure_protocol(selector, "wol", options)
    return {
        "status": "success",
        "deviceId": updated.device_id,
        "operationId": "wol.power.configure",
        "options": options,
    }


def _schedule_seconds(value: str | None) -> int:
    if not value:
        return 0
    text = str(value).strip()
    seconds = float(text) if text.replace(".", "", 1).isdigit() else duration(text)
    if not 0 <= seconds <= 86400:
        raise ValueError("el tiempo programado debe estar entre 0 y 24 horas")
    return math.ceil(seconds)


def _power_command(action: str, platform_name: str, seconds: int, force: bool, cancel: bool) -> str:
    if platform_name == "windows":
        if cancel:
            if action not in {"shutdown", "restart"}:
                raise ValueError("sólo shutdown/restart admiten --cancel")
            return "shutdown.exe /a"
        if action in {"shutdown", "restart"}:
            mode = "/s" if action == "shutdown" else "/r"
            return f"shutdown.exe {mode} /t {seconds}" + (" /f" if force else "")
        if seconds:
            raise ValueError("sleep/hibernate no admiten programación en Windows")
        return (
            "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"
            if action == "sleep"
            else "shutdown.exe /h"
        )
    if cancel:
        if action not in {"shutdown", "restart"}:
            raise ValueError("sólo shutdown/restart admiten --cancel")
        return "sudo -n shutdown -c"
    if action in {"shutdown", "restart"}:
        mode = "-h" if action == "shutdown" else "-r"
        moment = f"+{max(1, math.ceil(seconds / 60))}" if seconds else "now"
        return f"sudo -n shutdown {mode} {moment}"
    if seconds:
        raise ValueError("sleep/hibernate no admiten programación en Linux")
    return "systemctl suspend" if action == "sleep" else "systemctl hibernate"


def _power(args, database, selector: str, action: str) -> dict:
    started = utc_now()
    run_id = str(uuid.uuid4())
    device = database.resolve(selector)
    options = dict(device.protocol_options.get("wol", {}))
    if options.get("powerTransport") != "ssh":
        return result(
            f"wol.{action}",
            f"wol.{action}.transport",
            selector,
            "blocked",
            started,
            code="WOL.POWER.UNSUPPORTED",
            message="Configura el transporte SSH con 'wol NAME configure'",
            run_id=run_id,
        ).to_dict()
    method = str(_options(args, device)["method"])
    if not _condition_passes(args, device, database, method, 1):
        return result(
            f"wol.{action}",
            "wol.condition.evaluate",
            selector,
            "skipped",
            started,
            detail={"reason": "condition-false"},
            run_id=run_id,
        ).to_dict()
    if not args.yes and not args.dry_run:
        return result(
            f"wol.{action}",
            f"wol.{action}.confirm",
            selector,
            "blocked",
            started,
            code="WOL.POWER.CONFIRMATION_REQUIRED",
            message="usa --yes para confirmar",
            run_id=run_id,
        ).to_dict()
    seconds = _schedule_seconds(args.schedule)
    platform_name = str(options.get("powerPlatform", "")).casefold()
    if platform_name not in {"windows", "linux"}:
        raise ValueError("powerPlatform debe ser windows o linux")
    command = str(options.get("powerCommands", {}).get(action, "")).strip()
    if command:
        command = command.format(
            seconds=seconds,
            minutes=max(1, math.ceil(seconds / 60)) if seconds else 0,
            force="true" if args.force else "false",
        )
    else:
        command = _power_command(action, platform_name, seconds, args.force, args.cancel)
    if args.dry_run:
        return result(
            f"wol.{action}",
            f"wol.{action}.prepare",
            selector,
            "success",
            started,
            detail={"dryRun": True, "transport": "ssh", "command": command},
            run_id=run_id,
        ).to_dict()
    reference = device.credentials.get("ssh")
    if not reference:
        raise ValueError("el dispositivo no tiene credencial SSH")
    credential = CredentialStore(args.store).get(reference)
    profile = SshProfile.from_options(device.protocol_options.get("ssh", {}))
    try:
        exit_code, stdout, stderr = run_remote_command(
            device.ip,
            credential["username"],
            credential["password"],
            profile,
            command,
            timeout=min(120, max(5, float(args.timeout))),
        )
    except (OSError, ValueError) as error:
        return result(
            f"wol.{action}",
            f"wol.{action}.ssh",
            selector,
            "error",
            started,
            code="WOL.POWER.SSH_FAILED",
            message=str(error),
            run_id=run_id,
        ).to_dict()
    status = "success" if exit_code == 0 else "error"
    return result(
        f"wol.{action}",
        f"wol.{action}.ssh",
        selector,
        status,
        started,
        code=None if exit_code == 0 else "WOL.POWER.REMOTE_FAILED",
        message=stderr.strip() if exit_code else "",
        detail={
            "transport": "ssh",
            "exitCode": exit_code,
            "stdout": stdout.strip()[:2048],
            "scheduledSeconds": seconds,
        },
        run_id=run_id,
    ).to_dict()


def run_wol(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    known_devices = {}
    if args.words and args.words[0].casefold() == "sequence":
        payload = _sequence(args, database)
    else:
        if not args.words and not args.group and not args.all:
            raise ValueError("indica un elemento")
        action = args.words[1].casefold() if len(args.words) > 1 else "wakeup"
        if action == "configure":
            payload = _configure_power(args, database, args.words[0])
        elif action in POWER_ACTIONS:
            payload = _power(args, database, args.words[0], action)
        elif action == "status":
            device = database.resolve(args.words[0])
            online = _online(device, args.method or "auto", 1, args.check_port)
            payload = result(
                "wol.status",
                "wol.status.verify",
                args.words[0],
                "online" if online else "offline",
                utc_now(),
            ).to_dict()
        elif action == "wakeup":
            inventory = database.load()
            configured = load_config().get("wol", {})
            defaults = configured if isinstance(configured, dict) else {}
            if args.all:
                if not args.yes:
                    raise ValueError("--all requiere --yes")
                targets = inventory
            elif args.group:
                targets = [device for device in inventory if device.in_group(args.group)]
                if not targets:
                    raise ValueError(f"el grupo {args.group} no contiene dispositivos")
            else:
                targets = [database.resolve(args.words[0], devices=inventory)]
            known_devices = {device.device_id: device for device in targets}
            rows = [
                _wake(args, database, device, inventory=inventory, defaults=defaults)
                for device in targets
            ]
            payload = rows[0] if len(rows) == 1 else rows
        else:
            raise ValueError(f"acción wol no válida: {action}")
    write_log(
        f"WOL runId={payload[0]['runId'] if isinstance(payload, list) and payload else payload.get('runId', '-')} result={payload[-1]['status'] if isinstance(payload, list) and payload else payload.get('status', 'success')}"
    )
    for row in payload if isinstance(payload, list) else [payload]:
        if (
            row.get("taskId", "").startswith(("wol.wakeup", "sequence."))
            and row.get("operationId") != "wol.wakeup.prepare"
        ):
            try:
                device = known_devices.get(row["target"]) or database.resolve(row["target"])
                _write_wol_history(
                    device,
                    "wol.wakeup.result",
                    row["status"],
                    row.get("runId"),
                    row.get("taskId"),
                    row.get("operationId"),
                    row.get("error", {}).get("message", f"Wake-on-LAN: {row['status']}"),
                    row.get("error"),
                    row.get("durationMs"),
                )
            except (ValueError, OSError):
                pass
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif not args.quiet:
        rows = payload if isinstance(payload, list) else [payload]
        for row in rows:
            print(
                f"{row.get('taskId', row.get('sequence', 'wol'))} | {row.get('target', '-')} | {row['status'].upper()} | {row.get('operationId', '-')}"
            )
    statuses = (
        [x["status"] for x in payload] if isinstance(payload, list) else [payload.get("status")]
    )
    return (
        0 if all(x in {"success", "sent", "online", "skipped", "offline"} for x in statuses) else 1
    )


def _write_wol_history(
    device, event_type, status, run_id, task_id, operation_id, summary, error=None, duration=None
):
    with suppress(ValueError, OSError):
        HistoryService().write(
            HistoryEvent(
                event_type,
                "lanctl.network.wol",
                "local",
                status,
                summary,
                correlationId=run_id,
                runId=run_id,
                taskId=task_id,
                operationId=operation_id,
                device=DeviceSnapshot(
                    device.device_id,
                    device.mac,
                    device.ip,
                    device.alias or device.name or device.ip,
                ),
                error=error,
                durationMs=duration,
            )
        )
