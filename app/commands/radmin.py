from __future__ import annotations

import argparse
import json

from app.commands.open import run_open
from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.protocols.radmin import (
    COLOR_DEPTHS,
    DEFAULT_PORT,
    MODES,
    find_viewer,
    tcp_probe,
    validate_mode,
    validate_port,
)


def register_radmin_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser("radmin", help="Configura, comprueba o abre Radmin Viewer.")
    command.add_argument("selector", help="IP, MAC o alias del elemento.")
    command.add_argument("action", choices=("probe", "configure", "open"))
    command.add_argument("--mode", choices=MODES)
    command.add_argument("--port", type=int)
    command.add_argument(
        "--executable", help="Ruta por dispositivo; usa 'auto' para detección automática."
    )
    command.add_argument("--through", help="Servidor intermedio HOST:PUERTO.")
    command.add_argument(
        "--fullscreen", action="store_true", help="Abre control o vista a pantalla completa."
    )
    command.add_argument(
        "--color-depth",
        type=int,
        choices=COLOR_DEPTHS,
        help="Profundidad de color de Radmin (1, 2, 4, 8, 16 o 24 bits).",
    )
    command.add_argument(
        "--updates",
        type=int,
        help="Máximo de actualizaciones de pantalla por segundo (1-120).",
    )
    command.add_argument("--phonebook", help="Phonebook .rpb administrado por Radmin.")
    command.add_argument(
        "--phonebook-id",
        type=int,
        help="Identificador de entrada dentro del phonebook de Radmin.",
    )
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
        options["port"] = validate_port(
            args.port if args.port is not None else options.get("port", DEFAULT_PORT)
        )
        options["mode"] = validate_mode(args.mode or options.get("mode", "control"))
        if args.executable is not None:
            if args.executable.casefold() == "auto":
                options.pop("executable", None)
            else:
                options["executable"] = str(find_viewer(args.executable))
        for argument, key in (
            (args.through, "through"),
            (args.color_depth, "colorDepth"),
            (args.updates, "updates"),
            (args.phonebook, "phonebookPath"),
            (args.phonebook_id, "phonebookId"),
        ):
            if argument is not None:
                options[key] = argument
        if args.fullscreen:
            options["fullscreen"] = True
        database.configure_protocol(args.selector, "radmin", options)
        print(json.dumps(options, ensure_ascii=False))
        return 0
    if args.action == "probe":
        port = validate_port(
            args.port if args.port is not None else options.get("port", DEFAULT_PORT)
        )
        opened = tcp_probe(device.ip, port, float(load_config().get("timeout", 0.8)))
        print(
            json.dumps(
                {
                    "protocol": "radmin",
                    "ip": device.ip,
                    "port": port,
                    "open": opened,
                    "assessment": "probable/configurado" if opened else "no disponible",
                }
            )
        )
        return 0 if opened else 1
    return run_open(
        argparse.Namespace(
            selector=args.selector,
            protocol="radmin",
            port=args.port,
            mode=args.mode,
            path="",
            dry_run=False,
            database=args.database,
            store=args.store,
            through=args.through,
            fullscreen=args.fullscreen,
            color_depth=args.color_depth,
            updates=args.updates,
            phonebook=args.phonebook,
            phonebook_id=args.phonebook_id,
        )
    )
