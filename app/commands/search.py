from __future__ import annotations

import argparse
import json

from app.commands.call import public_device
from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.output import write_records

SEARCH_COLUMNS = (
    "ip",
    "cnf",
    "alias",
    "mac",
    "name",
    "group",
    "description",
    "manufacturer",
    "device-id",
    "protocols",
)


def register_search_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "search",
        help="Busca dispositivos por alias, nombre, IP o MAC.",
    )
    command.add_argument("selector", help="Alias, nombre, IP o MAC exactos.")
    command.add_argument(
        "--json",
        action="store_true",
        help="Devuelve el registro completo como JSON para scripts.",
    )
    command.add_argument(
        "--database", default=config["database"], help="Archivo JSON de elementos."
    )
    command.set_defaults(handler=run_search)


def run_search(args: argparse.Namespace) -> int:
    devices = DeviceDatabase(args.database).search(args.selector)
    if args.json:
        result = [public_device(device) for device in devices]
        print(
            json.dumps(
                result[0] if len(result) == 1 else result,
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        write_records(
            devices,
            output_format="table",
            columns=SEARCH_COLUMNS,
        )
    return 0
