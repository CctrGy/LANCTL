from __future__ import annotations

import argparse
import json

from app.commands.open import run_open
from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.protocols.radmin import DEFAULT_PORT, find_viewer, tcp_probe, validate_mode, validate_port


def register_radmin_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser("radmin", help="Configura, comprueba o abre Radmin Viewer.")
    command.add_argument("selector", help="IP, MAC o alias del elemento.")
    command.add_argument("action", choices=("probe", "configure", "open"))
    command.add_argument("--mode", choices=("control", "view"))
    command.add_argument("--port", type=int)
    command.add_argument("--executable", help="Ruta por dispositivo; usa 'auto' para detección automática.")
    command.add_argument("--database", default=config["database"])
    command.add_argument("--store", default=config["credentials"])
    for parser_action in command._actions:
        if parser_action.help is None:
            parser_action.help = "Opción de configuración de Radmin Viewer."
    command.set_defaults(handler=run_radmin)


def run_radmin(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    device = database.resolve(args.selector)
    options = dict(device.protocol_options.get("radmin", {}))
    if args.action == "configure":
        options["port"] = validate_port(args.port if args.port is not None else options.get("port", DEFAULT_PORT))
        options["mode"] = validate_mode(args.mode or options.get("mode", "control"))
        if args.executable is not None:
            if args.executable.casefold() == "auto":
                options.pop("executable", None)
            else:
                options["executable"] = str(find_viewer(args.executable))
        database.configure_protocol(args.selector, "radmin", options)
        print(json.dumps(options, ensure_ascii=False))
        return 0
    if args.action == "probe":
        port = validate_port(args.port if args.port is not None else options.get("port", DEFAULT_PORT))
        opened = tcp_probe(device.ip, port, float(load_config().get("timeout", 0.8)))
        print(json.dumps({"protocol": "radmin", "ip": device.ip, "port": port,
                          "open": opened, "assessment": "probable/configurado" if opened else "no disponible"}))
        return 0 if opened else 1
    return run_open(argparse.Namespace(selector=args.selector, protocol="radmin", port=args.port,
        mode=args.mode, path="", dry_run=False, database=args.database, store=args.store))
