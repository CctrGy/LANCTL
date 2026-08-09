from __future__ import annotations

import argparse
import json

from app.core.config import load_config
from app.core.database import DeviceDatabase

FIELDS = {
    "ip": "IP",
    "cnf": "cnf",
    "mac": "MAC",
    "alias": "ALIAS",
    "name": "NAME",
    "group": "GROUP",
    "description": "description",
    "manufacturer": "manufacturer",
    "default-name": "defaultName",
    "device-id": "deviceId",
    "protocols": "protocols",
}


def public_device(device) -> dict:
    return {
        "IP": device.ip,
        "cnf": device.cnf,
        "ALIAS": device.alias,
        "MAC": device.mac,
        "NAME": device.name,
        "GROUP": device.groups,
        "description": device.description,
        "manufacturer": device.manufacturer,
        "defaultName": device.default_name,
        "deviceId": device.device_id,
        "protocols": device.protocols,
        "credentials": device.credentials,
        "protocolOptions": device.protocol_options,
    }


def register_call_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "call",
        help="Resuelve un alias, una IP o una MAC a los datos del dispositivo.",
    )
    command.add_argument("selector", help="Alias, IP o MAC del dispositivo.")
    command.add_argument(
        "-f",
        "--field",
        choices=tuple(FIELDS),
        default="ip",
        help="Dato devuelto (por defecto: ip).",
    )
    command.add_argument(
        "--json",
        action="store_true",
        help="Devuelve el registro completo como JSON.",
    )
    command.add_argument(
        "--database", default=config["database"], help="Archivo JSON de elementos."
    )
    command.set_defaults(handler=run_call)


def run_call(args: argparse.Namespace) -> int:
    device = DeviceDatabase(args.database).resolve(args.selector)
    if args.json:
        print(json.dumps(public_device(device), indent=2, ensure_ascii=False))
    else:
        value = device[FIELDS[args.field]]
        print(",".join(value) if isinstance(value, list) else value)
    return 0
