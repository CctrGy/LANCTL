from __future__ import annotations

import argparse
import sys

from app import __version__
from app.commands.alias import register_alias_command
from app.commands.call import register_call_command
from app.commands.cnf import register_cnf_command
from app.commands.credential import register_credential_command
from app.commands.download_settings import (
    register_download_settings_command,
    register_gateway_command,
)
from app.commands.element import register_element_command
from app.commands.group import register_group_command
from app.commands.name import register_name_command
from app.commands.protocol import register_protocol_command
from app.commands.ssh import register_ssh_command
from app.commands.terminal import register_terminal_command
from app.commands.settings import register_settings_command
from app.commands.search import register_search_command
from app.commands.scan import register_scan_command
from app.commands.switch import register_switch_command
from app.commands.list import register_list_command
from app.commands.ping import register_ping_command
from app.commands.open import register_open_command
from app.commands.project import register_project_command
from app.commands.modes import register_virtual_mode, run_global_cli
from app.core.console import error as print_error, pending
from app.core.parser import LANCTLArgumentParser
from app.core.logger import write_log
from app.core.log_cleanup import run_automatic_log_cleanup


LEGACY_VIRTUAL_COMMANDS = {
    "list", "settings", "call", "search", "scan", "cnf", "credential",
    "credentials", "auth", "gateway", "downloadsettings", "download-settings",
    "protocol", "ssh", "terminal", "cli", "switch", "group", "element",
    "name", "alias", "ping", "open", "connect", "project", "projects",
}


def register_virtual_commands(commands: argparse._SubParsersAction) -> None:
    register_list_command(commands)
    register_ping_command(commands)
    register_open_command(commands)
    register_settings_command(commands)
    register_call_command(commands)
    register_search_command(commands)
    register_scan_command(commands)
    register_cnf_command(commands)
    register_credential_command(commands)
    register_gateway_command(commands)
    register_download_settings_command(commands)
    register_protocol_command(commands)
    register_ssh_command(commands)
    register_terminal_command(commands)
    register_switch_command(commands)
    register_group_command(commands)
    register_element_command(commands)
    register_name_command(commands)
    register_alias_command(commands)
    register_project_command(commands)


def build_parser() -> argparse.ArgumentParser:
    parser = LANCTLArgumentParser(
        prog="LANCTL",
        description="Control lógico de dispositivos e infraestructuras LAN.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión y termina.",
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Abre la interfaz gráfica de LANCTL (reservado para una versión futura).",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Abre la terminal interactiva persistente de LANCTL.",
    )
    parser.add_argument(
        "-tui",
        "--tui",
        action="store_true",
        help="Abre la interfaz avanzada de terminal a pantalla completa.",
    )
    commands = parser.add_subparsers(dest="command", metavar="ÁMBITO/COMANDO")
    register_virtual_mode(commands, register_virtual_commands)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0].casefold() in LEGACY_VIRTUAL_COMMANDS:
        arguments.insert(0, "virtual")
    run_automatic_log_cleanup()
    write_log(f"COMMAND LANCTL {' '.join(arguments)}".rstrip())
    parser = build_parser()
    args = parser.parse_args(arguments)

    try:
        if args.tui:
            from app.tui import run_tui
            return run_tui()
        if args.cli:
            return run_global_cli()
        if not args.command:
            pending(
                "La interfaz gráfica todavía no está disponible. "
                "Usa 'lanctl --cli' para abrir la terminal interactiva."
            )
            return 0
        return args.handler(args)
    except KeyboardInterrupt:
        print_error("Operación cancelada.")
        return 130
    except (OSError, ValueError) as error:
        print_error(str(error))
        return 2
