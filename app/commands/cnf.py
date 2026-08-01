from __future__ import annotations

import argparse

from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase


def register_cnf_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "cnf",
        help="Asigna el estado CNF de un elemento por IP, MAC o alias.",
    )
    command.add_argument("selector", help="IP, MAC o alias del elemento.")
    command.add_argument(
        "value",
        nargs="?",
        help=(
            "O (OK), X (UNKNOWN), - (UNRECOGNIZED), S (MARKED) o "
            "F (FIXED). Sin valor libera F y restaura O."
        ),
    )
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.set_defaults(handler=run_cnf)


def run_cnf(args: argparse.Namespace) -> int:
    current = DeviceDatabase(args.database).resolve(args.selector)
    value = args.value
    if value is None:
        if current.cnf != "F":
            ok(
                "SIN CAMBIOS",
                f"{current.alias or current.ip} | cnf = {current.cnf}",
            )
            return 0
        value = "O"
    device = DeviceDatabase(args.database).edit_device(
        args.selector, "cnf", value
    )
    ok("ACTUALIZADO", f"{device.alias or device.ip} | cnf = {device.cnf}")
    return 0
