from __future__ import annotations

import argparse
import json

from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase
from app.protocols.ssh import SSH_PROFILES, SshProfile


def register_protocol_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "protocol", help="Consulta o configura un protocolo de un elemento."
    )
    command.add_argument("selector", help="IP, MAC o alias.")
    command.add_argument(
        "action", choices=("show", "configure"), help="Consulta o modifica el protocolo."
    )
    command.add_argument("protocol", help="Protocolo que se configura.")
    command.add_argument("--port", type=int, default=22, help="Puerto remoto.")
    command.add_argument("--driver", default="autodetect", help="Controlador del dispositivo.")
    command.add_argument(
        "--host-key",
        action="append",
        default=[],
        help="Algoritmo de clave de host permitido; se puede repetir.",
    )
    command.add_argument(
        "--kex",
        action="append",
        default=[],
        help="Algoritmo de intercambio de claves; se puede repetir.",
    )
    command.add_argument("--profile", choices=tuple(SSH_PROFILES), help="Perfil SSH reutilizable.")
    command.add_argument(
        "--database", default=config["database"], help="Archivo JSON de elementos."
    )
    command.set_defaults(handler=run_protocol)


def run_protocol(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    device = database.resolve(args.selector)
    protocol = args.protocol.casefold()
    if args.action == "show":
        print(json.dumps(device.protocol_options.get(protocol, {}), indent=2))
        return 0
    if protocol != "ssh":
        raise ValueError("la configuración avanzada está implementada actualmente para ssh")
    options = (
        dict(SSH_PROFILES[args.profile])
        if args.profile
        else {
            "port": args.port,
            "driver": args.driver,
            "hostKeyAlgorithms": args.host_key,
            "kexAlgorithms": args.kex,
        }
    )
    SshProfile.from_options(options)
    updated = database.configure_protocol(args.selector, protocol, options)
    ok(
        "PROTOCOLO",
        f"{updated.alias or updated.ip} | ssh configurado solo para este elemento",
    )
    return 0
