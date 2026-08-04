from __future__ import annotations

import argparse
import json
import socket
import time
import uuid
from datetime import datetime
from pathlib import Path

from app.core.conditions import ConditionContext, duration, evaluate, parse_condition
from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.logger import write_log
from app.core.tasking import JsonStore, TASK_ID, result, utc_now
from app.core.history import DeviceSnapshot, HistoryEvent, HistoryService
from app.plugins.wol_runtime import send_magic_packet, validate_mac
from app.services.element_scanner import ping_details
from app.services.lan_scanner import active_arp_mac


POWER_ACTIONS = {"shutdown", "restart", "sleep", "hibernate"}
STATUSES = {"pending", "running", "success", "skipped", "blocked", "timeout", "cancelled", "error"}


def register_wol_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser("wol", help="Enciende equipos mediante Wake-on-LAN y ejecuta secuencias seguras.")
    command.add_argument("words", nargs="*", help="NAME [wakeup|status|shutdown|restart|sleep|hibernate] o sequence ...")
    command.add_argument("-if", "--if", dest="conditions", action="append", default=[], metavar="CONDICIÓN")
    command.add_argument("--if-all", action="append", default=[], metavar="CONDICIÓN")
    command.add_argument("--if-any", action="append", default=[], metavar="CONDICIÓN")
    command.add_argument("--if-not", action="append", default=[], metavar="CONDICIÓN")
    command.add_argument("-t", "--time", dest="schedule")
    command.add_argument("--message"); command.add_argument("--force", action="store_true"); command.add_argument("--cancel", action="store_true")
    command.add_argument("--broadcast", default=None); command.add_argument("--port", type=int, default=None)
    command.add_argument("--repeat", type=int, default=None); command.add_argument("--interval", type=float, default=None)
    command.add_argument("--wait", type=float, default=None); command.add_argument("--method", choices=("auto", "arp", "ping", "port"), default=None)
    command.add_argument("--check-port", type=int, default=None); command.add_argument("--interface")
    command.add_argument("--retry", type=int, default=0); command.add_argument("--dry-run", action="store_true")
    command.add_argument("--json", action="store_true"); command.add_argument("--quiet", action="store_true")
    command.add_argument("--group"); command.add_argument("--all", action="store_true"); command.add_argument("--yes", action="store_true")
    command.add_argument("--after", action="append", default=[]); command.add_argument("--delay")
    command.add_argument("--timeout", type=float, default=60); command.add_argument("--on-failure", choices=("stop", "continue", "retry"), default="stop")
    command.add_argument("--cooldown"); command.add_argument("--max-attempts", type=int, default=1)
    command.add_argument("--database", default=config["database"])
    command.add_argument("--sequences", default=config.get("wolSequences", "data/lc/wol-sequences.json"))
    help_by_dest = {
        "conditions":"Condición AND adicional (repetible).", "if_all":"Condición AND adicional.",
        "if_any":"Condición OR adicional.", "if_not":"Condición negada.", "schedule":"Momento del apagado programado.",
        "message":"Mensaje remoto, si el transporte lo admite.", "force":"Solicita cierre forzado al transporte.",
        "cancel":"Cancela una programación, si el transporte lo admite.", "broadcast":"IPv4 de broadcast.",
        "port":"Puerto UDP WOL.", "repeat":"Número de paquetes mágicos.", "interval":"Intervalo entre paquetes.",
        "wait":"Segundos máximos de verificación.", "method":"Método de verificación.", "check_port":"Puerto TCP de comprobación.",
        "interface":"IPv4 local de salida.", "retry":"Reintentos completos.", "dry_run":"Valida sin enviar.",
        "json":"Salida JSON estructurada.", "quiet":"Omite salida humana.", "group":"Actúa sobre un grupo.",
        "all":"Actúa sobre todo el inventario.", "yes":"Confirma explícitamente --all.", "after":"Dependencia de paso.",
        "delay":"Espera previa del paso.", "timeout":"Timeout de paso.", "on_failure":"Política ante fallo.",
        "cooldown":"Espera mínima entre ejecuciones.", "max_attempts":"Máximo de intentos.",
        "database":"Archivo JSON de elementos.", "sequences":"Archivo transaccional de secuencias.",
    }
    for parser_action in command._actions:
        if parser_action.help is None:
            parser_action.help = help_by_dest.get(parser_action.dest, "Opción Wake-on-LAN.")
    command.set_defaults(handler=run_wol)


def _online(device, method: str, timeout: float, check_port: int | None) -> bool:
    if not device.ip or device.ip == "-": return False
    if method in {"auto", "arp"} and active_arp_mac(device.ip, min(timeout, 1.0)):
        return True
    if method in {"auto", "ping"} and ping_details(device.ip, min(timeout, 1.0))[0]:
        return True
    if method == "port":
        if check_port is None: raise ValueError("--method port requiere --check-port")
        try:
            with socket.create_connection((device.ip, check_port), timeout=min(timeout, 1.0)): return True
        except OSError: return False
    return False


def _options(args, device) -> dict:
    config = load_config(); defaults = config.get("wol", {}) if isinstance(config.get("wol"), dict) else {}
    local = device.protocol_options.get("wol", {})
    values = {"broadcast": "255.255.255.255", "port": 9, "repeat": 3, "interval": .5, "wait": 60, "method": "auto"}
    values.update(defaults); values.update(local)
    for arg, key in ((args.broadcast,"broadcast"),(args.port,"port"),(args.repeat,"repeat"),(args.interval,"interval"),(args.wait,"wait"),(args.method,"method")):
        if arg is not None: values[key] = arg
    if not 0 <= float(values["wait"]) <= 3600: raise ValueError("wait debe estar entre 0 y 3600 segundos")
    if not 0 <= args.retry <= 10: raise ValueError("retry debe estar entre 0 y 10")
    if args.check_port is not None and not 1 <= args.check_port <= 65535: raise ValueError("check-port fuera de 1..65535")
    return values


def _condition_passes(args, device, database, method, timeout) -> bool:
    online = lambda selector: _online(database.resolve(selector), method, timeout, args.check_port)
    context = ConditionContext(online=online, target=device.device_id, last_seen=device.last_seen,
        group_members=lambda name: [d.device_id for d in database.load() if name.casefold() in (g.casefold() for g in d.groups)])
    all_conditions = [parse_condition(x) for x in args.conditions + args.if_all]
    any_conditions = [parse_condition(x) for x in args.if_any]
    not_conditions = [parse_condition(x) for x in args.if_not]
    return all(evaluate(x, context) for x in all_conditions) and (not any_conditions or any(evaluate(x, context) for x in any_conditions)) and not any(evaluate(x, context) for x in not_conditions)


def _wake(args, database, selector: str, *, task_id="wol.wakeup") -> dict:
    started = utc_now(); run_id = str(uuid.uuid4())
    try: device = database.resolve(selector)
    except ValueError as error:
        return result(task_id, "wol.resolve.device", selector, "error", started, code="WOL.RESOLVE.DEVICE", message=str(error), run_id=run_id).to_dict()
    try: validate_mac(device.mac)
    except ValueError as error:
        return result(task_id, "wol.resolve.mac", selector, "invalid", started, code="WOL.MAC.INVALID", message=str(error), run_id=run_id).to_dict()
    options = _options(args, device); method = str(options["method"])
    if not _condition_passes(args, device, database, method, min(float(options["wait"]), 1)):
        return result(task_id, "wol.condition.evaluate", selector, "skipped", started, detail={"reason":"condition-false"}, run_id=run_id).to_dict()
    already = _online(device, method, 1, args.check_port)
    if args.dry_run:
        status = "online" if already else "sent"
        return result(task_id, "wol.wakeup.prepare", selector, status, started, detail={**options,"dryRun":True,"mac":device.mac}, run_id=run_id).to_dict()
    try:
        for attempt in range(args.retry + 1):
            send_magic_packet(device.mac, options["broadcast"], options["port"], options["repeat"], options["interval"], args.interface)
            _write_wol_history(device, "wol.wakeup.sent", "sent", run_id, task_id, "wol.wakeup.send", "Paquete Wake-on-LAN enviado")
            if already or not options["wait"]: break
            deadline = time.monotonic() + float(options["wait"])
            while time.monotonic() < deadline:
                if _online(device, method, 1, args.check_port):
                    return result(task_id, "wol.wakeup.verify", selector, "online", started, detail={"attempt":attempt+1,"sent":True}, run_id=run_id).to_dict()
                time.sleep(min(1, max(0, deadline-time.monotonic())))
        if already: return result(task_id, "wol.wakeup.verify", selector, "online", started, detail={"alreadyOnline":True,"sent":True}, run_id=run_id).to_dict()
        if not options["wait"]: return result(task_id, "wol.wakeup.send", selector, "sent", started, detail={"confirmed":False}, run_id=run_id).to_dict()
        return result(task_id, "wol.wakeup.verify", selector, "timeout", started, code="WOL.VERIFY.TIMEOUT", message="El dispositivo no fue detectado; el paquete enviado no garantiza el encendido", run_id=run_id).to_dict()
    except Exception as error:
        return result(task_id, "wol.wakeup.send", selector, "error", started, code="WOL.SEND.ERROR", message=str(error), run_id=run_id).to_dict()


def _sequence(args, database) -> dict | list:
    if len(args.words) < 2: raise ValueError("usa wol sequence create ID o wol sequence ID run")
    store = JsonStore(args.sequences); data = store.load(); words = args.words[1:]
    if words[0] == "create":
        if len(words) != 2 or not TASK_ID.fullmatch(words[1]): raise ValueError("id de secuencia no válido")
        if words[1] in data["sequences"]: raise ValueError("la secuencia ya existe")
        data["sequences"][words[1]] = {"id":words[1],"steps":[],"cooldown":args.cooldown,"maxAttempts":args.max_attempts}; store.save(data)
        return {"status":"success","sequence":words[1]}
    sequence_id = words[0]
    if sequence_id not in data["sequences"]: raise ValueError("secuencia no encontrada")
    sequence = data["sequences"][sequence_id]; action = words[1] if len(words)>1 else "run"
    if action == "add":
        if len(words)<3: raise ValueError("falta el objetivo del paso")
        target=words[2]; step_id=target.casefold().replace(" ","-")
        step={"id":step_id,"action":"wakeup","target":target,"requires":[x.casefold().replace(" ","-") for x in args.after],"delay":args.delay,"wait":"online","timeout":args.timeout,"retry":args.retry,"onFailure":args.on_failure}
        if any(x["id"]==step_id for x in sequence["steps"]): raise ValueError("el paso ya existe")
        sequence["steps"].append(step); _validate_graph(sequence["steps"]); store.save(data)
        return {"status":"success","sequence":sequence_id,"step":step}
    if action != "run": raise ValueError("acción de secuencia no soportada")
    _validate_graph(sequence["steps"]); states={}; results=[]
    pending=list(sequence["steps"])
    while pending:
        progressed=False
        for step in list(pending):
            if any(dep not in states for dep in step["requires"]): continue
            pending.remove(step); progressed=True
            failed=next((dep for dep in step["requires"] if states[dep] not in {"success","online","sent","skipped"}),None)
            if failed:
                row=result(f"sequence.{sequence_id}.{step['id']}","wol.sequence.dependency",step["target"],"blocked",utc_now(),code="WOL.SEQUENCE.BLOCKED",message="Dependencia no completada",dependency=failed).to_dict()
            else:
                if step.get("delay"): time.sleep(duration(step["delay"]))
                row=_wake(args,database,step["target"],task_id=f"sequence.{sequence_id}.{step['id']}")
            states[step["id"]]=row["status"]; results.append(row)
        if not progressed: raise ValueError("dependencias de secuencia irresolubles")
    data["runs"][results[0]["runId"] if results else str(uuid.uuid4())]={"sequence":sequence_id,"results":results}; store.save(data)
    return results


def _validate_graph(steps: list[dict]) -> None:
    ids={x["id"] for x in steps}
    if any(dep not in ids for step in steps for dep in step.get("requires",[])): raise ValueError("dependencia de secuencia inexistente")
    visiting=set(); done=set(); mapping={x["id"]:x.get("requires",[]) for x in steps}
    def visit(node):
        if node in visiting: raise ValueError("la secuencia contiene un ciclo")
        if node in done:return
        visiting.add(node)
        for dep in mapping[node]:visit(dep)
        visiting.remove(node);done.add(node)
    for node in mapping:visit(node)


def run_wol(args: argparse.Namespace) -> int:
    database=DeviceDatabase(args.database)
    if args.words and args.words[0].casefold()=="sequence": payload=_sequence(args,database)
    else:
        if not args.words and not args.group and not args.all: raise ValueError("indica un elemento")
        action=args.words[1].casefold() if len(args.words)>1 else "wakeup"
        if action in POWER_ACTIONS:
            started=utc_now(); target=args.words[0]
            payload=result(f"wol.{action}",f"wol.{action}.transport",target,"blocked",started,code="WOL.POWER.UNSUPPORTED",message="No hay un transporte remoto autorizado configurado para esta acción").to_dict()
        elif action=="status":
            device=database.resolve(args.words[0]); online=_online(device,args.method or "auto",1,args.check_port)
            payload=result("wol.status","wol.status.verify",args.words[0],"online" if online else "offline",utc_now()).to_dict()
        elif action=="wakeup":
            if args.all:
                if not args.yes: raise ValueError("--all requiere --yes")
                targets=database.load()
            elif args.group:
                targets=[device for device in database.load() if args.group.casefold() in (group.casefold() for group in device.groups)]
                if not targets: raise ValueError(f"el grupo {args.group} no contiene dispositivos")
            else: targets=[database.resolve(args.words[0])]
            rows=[_wake(args,database,device.device_id) for device in targets]
            payload=rows[0] if len(rows)==1 else rows
        else: raise ValueError(f"acción wol no válida: {action}")
    write_log(f"WOL runId={payload[0]['runId'] if isinstance(payload,list) and payload else payload.get('runId','-')} result={payload[-1]['status'] if isinstance(payload,list) and payload else payload.get('status','success')}")
    for row in (payload if isinstance(payload,list) else [payload]):
        if row.get("taskId","").startswith(("wol.wakeup","sequence.")) and row.get("operationId") != "wol.wakeup.prepare":
            try:
                device=database.resolve(row["target"])
                _write_wol_history(device,"wol.wakeup.result",row["status"],row.get("runId"),row.get("taskId"),row.get("operationId"),row.get("error",{}).get("message",f"Wake-on-LAN: {row['status']}"),row.get("error"),row.get("durationMs"))
            except (ValueError,OSError): pass
    if args.json: print(json.dumps(payload,indent=2,ensure_ascii=False))
    elif not args.quiet:
        rows=payload if isinstance(payload,list) else [payload]
        for row in rows: print(f"{row.get('taskId',row.get('sequence','wol'))} | {row.get('target','-')} | {row['status'].upper()} | {row.get('operationId','-')}")
    statuses=[x["status"] for x in payload] if isinstance(payload,list) else [payload.get("status")]
    return 0 if all(x in {"success","sent","online","skipped","offline"} for x in statuses) else 1


def _write_wol_history(device, event_type, status, run_id, task_id, operation_id, summary, error=None, duration=None):
    try:
        HistoryService().write(HistoryEvent(event_type,"lanctl.network.wol","local",status,summary,
            correlationId=run_id,runId=run_id,taskId=task_id,operationId=operation_id,
            device=DeviceSnapshot(device.device_id,device.mac,device.ip,device.alias or device.name or device.ip),
            error=error,durationMs=duration))
    except (ValueError,OSError):
        pass
