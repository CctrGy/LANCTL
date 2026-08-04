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
from app.commands.radmin import register_radmin_command
from app.commands.wol import register_wol_command
from app.commands.history import register_history_command
from app.commands.monitor import register_monitor_command
from app.commands.smb import register_smb_command
from app.commands.terminal import register_terminal_command
from app.commands.settings import register_settings_command
from app.commands.search import register_search_command
from app.commands.scan import register_scan_command
from app.commands.switch import register_switch_command
from app.commands.list import register_list_command
from app.commands.recurrent import register_recurrent_command
from app.commands.ping import register_ping_command
from app.commands.open import register_open_command
from app.commands.project import register_project_command
from app.commands.plugin import register_plugin_command
from app.commands.language import register_language_command
from app.commands.modes import register_virtual_mode, run_global_cli
from app.core.console import error as print_error
from app.core.parser import LANCTLArgumentParser
from app.core.logger import write_log
from app.core.log_cleanup import run_automatic_log_cleanup


LEGACY_VIRTUAL_COMMANDS = {
    "list", "settings", "call", "search", "scan", "cnf", "credential",
    "credentials", "auth", "gateway", "downloadsettings", "download-settings",
    "protocol", "ssh", "radmin", "wol", "history", "monitor", "terminal", "cli", "switch", "group", "element",
    "name", "alias", "ping", "open", "connect", "project", "projects",
    "plugin", "plugins", "addon", "addons",
    "language", "languages", "lang", "recurrent", "smb",
}


def register_virtual_commands(commands: argparse._SubParsersAction) -> None:
    register_list_command(commands)
    register_recurrent_command(commands)
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
    register_radmin_command(commands)
    register_wol_command(commands)
    register_history_command(commands)
    register_monitor_command(commands)
    register_smb_command(commands)
    register_terminal_command(commands)
    register_switch_command(commands)
    register_group_command(commands)
    register_element_command(commands)
    register_name_command(commands)
    register_alias_command(commands)
    register_project_command(commands)
    register_plugin_command(commands)
    register_language_command(commands)
    from app.plugins.declarative_commands import register_declarative_commands
    register_declarative_commands(commands)


def build_parser() -> argparse.ArgumentParser:
    from app.i18n import t
    parser = LANCTLArgumentParser(
        prog="LANCTL",
        description=t("LANCTL.CORE.APP.DESCRIPTION"),
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
        help=t("LANCTL.CORE.APP.GUI_RESERVED"),
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help=t("LANCTL.CORE.APP.CLI_HELP"),
    )
    parser.add_argument(
        "-tui",
        "--tui",
        action="store_true",
        help=t("LANCTL.CORE.APP.TUI_HELP"),
    )
    commands = parser.add_subparsers(dest="command", metavar="ÁMBITO/COMANDO")
    register_virtual_mode(commands, register_virtual_commands)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    run_automatic_log_cleanup()
    from app.i18n import initialize_language, t
    initialize_language()
    from app.assets.icons import initialize_icons
    initialize_icons()
    from app.plugins import get_plugin_manager
    manager = get_plugin_manager()
    if not load_plugin_safe_mode() and manager.activate_enabled():
        mode = "tui" if any(v in arguments for v in ("-tui", "--tui")) else "cli" if "--cli" in arguments else "gui" if "--gui" in arguments or not arguments else "command"
        manager.events.emit(
            "LANCTL.Core.Lifecycle.Startup",
            {"version": __version__, "mode": mode},
        )
    plugin_commands = {
        str(item.specification.get("name", "")).casefold()
        for item in manager.extensions.list("command")
    }
    plugin_commands.update(
        str(alias).casefold()
        for item in manager.extensions.list("command")
        for alias in item.specification.get("aliases", [])
    )
    if arguments and arguments[0].casefold() in LEGACY_VIRTUAL_COMMANDS | plugin_commands:
        arguments.insert(0, "virtual")
    write_log(f"COMMAND LANCTL {' '.join(arguments)}".rstrip())
    parser = build_parser()
    args = parser.parse_args(arguments)

    try:
        if args.gui or (not args.command and not args.tui and not args.cli):
            from app.gui import run_gui
            return run_gui()
        if args.tui:
            from app.tui import run_tui
            return run_tui()
        if args.cli:
            return run_global_cli()
        return args.handler(args)
    except KeyboardInterrupt:
        print_error(t("LANCTL.CORE.APP.CANCELLED"))
        return 130
    except (OSError, RuntimeError, ValueError) as error:
        print_error(str(error))
        return 2


def load_plugin_safe_mode() -> bool:
    from app.core.config import load_config
    return bool(load_config().get("pluginSafeMode", False))
