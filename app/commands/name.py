from __future__ import annotations

import argparse

from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase


def add_edit_arguments(command: argparse.ArgumentParser) -> None:
    command.add_argument("selector", help="MAC, IP o alias del dispositivo.")
    actions = command.add_mutually_exclusive_group(required=True)
    actions.add_argument("value", nargs="?", help="Nuevo valor.")
    actions.add_argument(
        "-def", dest="use_default", action="store_true", help="Restaura el valor predeterminado."
    )
    actions.add_argument(
        "-del", dest="delete", action="store_true", help="Deja el valor en blanco."
    )
    command.add_argument(
        "--database",
        default=load_config()["database"],
        help="Base de datos JSON.",
    )


def selected_action(args: argparse.Namespace) -> tuple[str, str]:
    if args.use_default:
        return "default", ""
    if args.delete:
        return "delete", ""
    return "value", args.value


def register_name_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "name",
        help="Edita NAME usando una MAC, IP o alias.",
    )
    add_edit_arguments(command)
    command.set_defaults(handler=run_name)


def run_name(args: argparse.Namespace) -> int:
    mode, value = selected_action(args)
    device = DeviceDatabase(args.database).set_value(args.selector, "NAME", mode, value)
    value = device["NAME"] or "(vacío)"
    ok("ACTUALIZADO", f'{device["ALIAS"] or device["IP"]} | NAME = "{value}"')
    return 0
