from __future__ import annotations

import argparse

from app.commands.name import add_edit_arguments, selected_action
from app.core.console import ok
from app.core.database import DeviceDatabase


def register_alias_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "alias",
        help="Edita ALIAS usando una MAC, IP o alias actual.",
    )
    add_edit_arguments(command)
    command.set_defaults(handler=run_alias)


def run_alias(args: argparse.Namespace) -> int:
    mode, value = selected_action(args)
    device = DeviceDatabase(args.database).set_value(args.selector, "ALIAS", mode, value)
    value = device["ALIAS"] or "(vacío)"
    ok("ACTUALIZADO", f'{device["IP"]} | ALIAS = "{value}"')
    return 0
