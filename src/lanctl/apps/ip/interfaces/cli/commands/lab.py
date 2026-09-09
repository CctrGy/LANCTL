from __future__ import annotations

import argparse
import csv
import io
import json
import sys

from lanctl.apps.ip.lab import LabRepository, generate_scenario, validate_scenario
from lanctl.core.console import ok
from lanctl.core.file_transaction import atomic_write_json, atomic_write_text


def register_lab_command(commands: argparse._SubParsersAction) -> None:
    lab = commands.add_parser("lab", help="Gestiona redes LAN simuladas sin tráfico real.")
    actions = lab.add_subparsers(dest="lab_action", required=True, metavar="ACCIÓN")
    generate = actions.add_parser("generate", help="Genera un escenario reproducible.")
    generate.add_argument("--name", default="lab", help="Nombre del escenario.")
    generate.add_argument("--cidr", default="192.0.2.0/24", help="Red IPv4 virtual.")
    generate.add_argument(
        "--profile",
        choices=("home", "office", "datacenter", "industrial", "chaotic"),
        default="home",
        help="Perfil de dispositivos.",
    )
    generate.add_argument("--devices", type=int, default=20, help="Cantidad de dispositivos.")
    generate.add_argument("--seed", type=int, default=1, help="Semilla reproducible.")
    generate.add_argument("--active-percent", type=float, default=80, help="Porcentaje activo.")
    generate.add_argument("--dhcp-percent", type=float, default=70, help="Porcentaje DHCP.")
    generate.add_argument(
        "--type",
        choices=("snapshot", "timeline", "chaos"),
        default="snapshot",
        help="Evolución del escenario.",
    )
    generate.set_defaults(handler=run_lab)
    for name, help_text in (
        ("list", "Lista escenarios."),
        ("status", "Muestra el escenario activo."),
        ("stop", "Desactiva el proveedor simulado."),
    ):
        actions.add_parser(name, help=help_text).set_defaults(handler=run_lab)
    start = actions.add_parser("start", help="Activa explícitamente un escenario virtual.")
    start.add_argument("scenario", help="Nombre del escenario.")
    start.set_defaults(handler=run_lab)
    validate = actions.add_parser("validate", help="Valida un escenario.")
    validate.add_argument("scenario", help="Nombre del escenario.")
    validate.set_defaults(handler=run_lab)
    export = actions.add_parser("export", help="Exporta un escenario.")
    export.add_argument("scenario", help="Nombre del escenario.")
    export.add_argument(
        "--format", choices=("json", "csv"), default="json", help="Formato de salida."
    )
    export.add_argument("--output", help="Archivo de destino; stdout si se omite.")
    export.set_defaults(handler=run_lab)
    imported = actions.add_parser("import", help="Importa un escenario JSON.")
    imported.add_argument("file", help="Archivo JSON.")
    imported.set_defaults(handler=run_lab)
    network = actions.add_parser("network", help="Crea manualmente una red virtual.")
    network_actions = network.add_subparsers(dest="network_action", required=True)
    create = network_actions.add_parser("create", help="Crea un escenario vacío.")
    create.add_argument("--name", required=True, help="Nombre del escenario.")
    create.add_argument("--cidr", default="192.0.2.0/24", help="CIDR virtual.")
    create.set_defaults(handler=run_lab)
    device = actions.add_parser("device", help="Edita dispositivos simulados.")
    device_actions = device.add_subparsers(dest="device_action", required=True)
    add = device_actions.add_parser("add", help="Añade un dispositivo.")
    add.add_argument("scenario", help="Escenario.")
    add.add_argument("--ip", required=True, help="IPv4 simulada.")
    add.add_argument("--mac", required=True, help="MAC simulada.")
    add.add_argument("--alias", default="", help="Alias.")
    add.add_argument("--name", default="", help="Nombre.")
    add.add_argument("--inactive", action="store_true", help="Lo crea inactivo.")
    add.set_defaults(handler=run_lab)
    delete = device_actions.add_parser("delete", help="Elimina un dispositivo.")
    delete.add_argument("scenario", help="Escenario.")
    delete.add_argument("device", help="ID, IP, MAC o alias.")
    delete.set_defaults(handler=run_lab)
    evolve = actions.add_parser("evolve", help="Avanza el reloj y aplica eventos pendientes.")
    evolve.add_argument("--seconds", type=float, required=True, help="Segundos virtuales.")
    evolve.set_defaults(handler=run_lab)


def _emit(event: str, payload: dict) -> None:
    try:
        from lanctl.core.plugins import get_plugin_manager

        get_plugin_manager().events.emit(event, payload)
    except (ImportError, OSError, PermissionError, RuntimeError, ValueError):
        pass


def run_lab(args) -> int:
    repository = LabRepository()
    action = args.lab_action
    if action == "network":
        scenario = generate_scenario(name=args.name, cidr=args.cidr, devices=1, seed=0)
        scenario["devices"] = []
        repository.save(scenario)
        ok("LANLAB", f"Red virtual creada: {args.name} | {scenario['cidr']}")
        return 0
    if action == "device":
        scenario = repository.load(args.scenario)
        if args.device_action == "add":
            index = len(scenario["devices"]) + 1
            scenario["devices"].append(
                {
                    "id": f"manual-{index:04d}",
                    "ip": args.ip,
                    "mac": args.mac,
                    "active": not args.inactive,
                    "cnf": "X",
                    "alias": args.alias,
                    "name": args.name,
                    "hostname": "",
                    "group": "LAB",
                    "description": "Elemento simulado",
                    "manufacturer": "LANLAB",
                    "kind": "manual",
                    "confidence": 1.0,
                    "evidence": ["manual"],
                    "methods": ["SIMULATED"],
                    "ttl": 64,
                    "latencyMs": 1.0,
                    "lossPercent": 0.0,
                    "assignment": "static",
                    "ports": [],
                    "credentialRef": "SIMULATED-ONLY",
                }
            )
            repository.save(validate_scenario(scenario))
            ok("LANLAB", f"Dispositivo añadido: {args.ip}")
            return 0
        before = len(scenario["devices"])
        selector = args.device.casefold()
        scenario["devices"] = [
            row
            for row in scenario["devices"]
            if selector
            not in {str(row.get(key, "")).casefold() for key in ("id", "ip", "mac", "alias")}
        ]
        if len(scenario["devices"]) == before:
            raise ValueError(f"dispositivo simulado no encontrado: {args.device}")
        repository.save(scenario)
        ok("LANLAB", f"Dispositivo eliminado: {args.device}")
        return 0
    if action == "evolve":
        scenario = repository.active()
        if not scenario:
            raise ValueError("no hay escenario LANLAB activo")
        previous = float(scenario.get("clock", 0))
        scenario["clock"] = previous + max(0, args.seconds)
        by_id = {row["id"]: row for row in scenario["devices"]}
        for event in scenario.get("events", []):
            if previous < float(event["at"]) <= scenario["clock"] and event["deviceId"] in by_id:
                row = by_id[event["deviceId"]]
                if event["action"] in ("online", "offline"):
                    row["active"] = event["action"] == "online"
                elif event["action"] == "latency":
                    row["latencyMs"] = event["value"]
        repository.save(scenario)
        _emit(
            "LANCTL.Network.Lab.Tick",
            {
                "scenario_id": scenario["id"],
                "seed": scenario.get("seed"),
                "clock": scenario["clock"],
            },
        )
        ok("LANLAB", f"Reloj virtual: {scenario['clock']:.1f}s")
        return 0
    if action == "generate":
        scenario = generate_scenario(
            name=args.name,
            cidr=args.cidr,
            profile=args.profile,
            devices=args.devices,
            seed=args.seed,
            active_percent=args.active_percent,
            dhcp_percent=args.dhcp_percent,
            mode=args.type,
        )
        path = repository.save(scenario)
        _emit("LANCTL.Network.Lab.Created", {"scenario_id": scenario["id"], "path": str(path)})
        ok("LANLAB", f"{args.name} | {args.devices} dispositivos | seed {args.seed}")
        print(f" Archivo: {path}")
        return 0
    if action == "list":
        active = repository.active_name()
        for name in repository.names():
            print(f"{'*' if name == active else ' '} {name}")
        return 0
    if action == "start":
        scenario = repository.load(args.scenario)
        repository.set_active(args.scenario)
        _emit(
            "LANCTL.Network.Lab.Start",
            {"scenario_id": scenario["id"], "seed": scenario.get("seed")},
        )
        ok("LANLAB ACTIVO", f"{args.scenario} | puramente virtual")
        return 0
    if action == "stop":
        scenario = repository.active()
        repository.set_active(None)
        if scenario:
            _emit(
                "LANCTL.Network.Lab.Stop",
                {"scenario_id": scenario["id"], "seed": scenario.get("seed")},
            )
        ok("LANLAB", "Proveedor simulado desactivado")
        return 0
    if action == "status":
        scenario = repository.active()
        print(json.dumps(scenario or {"active": False}, ensure_ascii=False, indent=2))
        return 0
    if action == "validate":
        scenario = repository.load(args.scenario)
        validate_scenario(scenario)
        ok("LANLAB VÁLIDO", f"{args.scenario} | {len(scenario['devices'])} dispositivos")
        return 0
    if action == "import":
        with open(args.file, encoding="utf-8") as stream:
            scenario = validate_scenario(json.load(stream))
        repository.save(scenario)
        ok("LANLAB IMPORTADO", scenario["name"])
        return 0
    scenario = repository.load(args.scenario)
    if args.format == "json":
        text = json.dumps(scenario, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            atomic_write_json(args.output, scenario)
        else:
            sys.stdout.write(text)
    else:
        target = io.StringIO(newline="")
        writer = csv.DictWriter(
            target, fieldnames=("id", "ip", "mac", "active", "alias", "name", "kind")
        )
        writer.writeheader()
        writer.writerows(
            {key: row.get(key, "") for key in writer.fieldnames} for row in scenario["devices"]
        )
        if args.output:
            atomic_write_text(args.output, target.getvalue())
        else:
            sys.stdout.write(target.getvalue())
    return 0
