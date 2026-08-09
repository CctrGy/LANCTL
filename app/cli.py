from __future__ import annotations

import argparse
import sys
from contextlib import suppress
from importlib import import_module

from app import __version__
from app.core.log_cleanup import run_automatic_log_cleanup
from app.core.logger import write_log

# El registro usa nombres importables para que `lanctl --version` no cargue
# drivers de red, GUI, SSH y plugins antes de saber qué modo se ha solicitado.
_COMMAND_REGISTRARS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("app.commands.list", ("register_list_command",)),
    ("app.commands.recurrent", ("register_recurrent_command",)),
    ("app.commands.ping", ("register_ping_command",)),
    ("app.commands.open", ("register_open_command",)),
    ("app.commands.settings", ("register_settings_command",)),
    ("app.commands.call", ("register_call_command",)),
    ("app.commands.search", ("register_search_command",)),
    ("app.commands.scan", ("register_scan_command",)),
    ("app.commands.cnf", ("register_cnf_command",)),
    ("app.commands.credential", ("register_credential_command",)),
    (
        "app.commands.download_settings",
        ("register_gateway_command", "register_download_settings_command"),
    ),
    ("app.commands.protocol", ("register_protocol_command",)),
    ("app.commands.ssh", ("register_ssh_command",)),
    ("app.commands.radmin", ("register_radmin_command",)),
    ("app.commands.wol", ("register_wol_command",)),
    ("app.commands.history", ("register_history_command",)),
    ("app.commands.monitor", ("register_monitor_command",)),
    ("app.commands.access", ("register_access_command",)),
    ("app.commands.smb", ("register_smb_command",)),
    ("app.commands.terminal", ("register_terminal_command",)),
    ("app.commands.switch", ("register_switch_command",)),
    ("app.commands.group", ("register_group_command",)),
    ("app.commands.element", ("register_element_command",)),
    ("app.commands.name", ("register_name_command",)),
    ("app.commands.alias", ("register_alias_command",)),
    ("app.commands.project", ("register_project_command",)),
    ("app.commands.plugin", ("register_plugin_command",)),
    ("app.commands.language", ("register_language_command",)),
)


def configure_utf8_stdio() -> None:
    """Normaliza la salida textual, incluida la que se redirige a otro proceso."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            # Consolas embebidas y algunos lanzadores no permiten
            # reconfigurar el flujo; en ellos se conserva el contrato dado.
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def register_commands(
    commands: argparse._SubParsersAction, include_plugin_commands: bool = False
) -> None:
    for module_name, registrar_names in _COMMAND_REGISTRARS:
        module = import_module(module_name)
        for registrar_name in registrar_names:
            getattr(module, registrar_name)(commands)
    if include_plugin_commands:
        from app.plugins.declarative_commands import register_declarative_commands

        register_declarative_commands(commands)


def run_global_cli() -> int:
    """Carga la consola persistente únicamente cuando se solicita ``--cli``."""

    from app.commands.modes import run_global_cli as run

    return run()


def print_error(message: str) -> None:
    """Evita cargar Colorama durante rutas rápidas como ``--version``."""

    from app.core.console import error

    error(message)


def build_parser(include_plugin_commands: bool = False) -> argparse.ArgumentParser:
    from app.core.parser import LANCTLArgumentParser
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
    parser.add_argument(
        "-project",
        "--project",
        dest="startup_project",
        metavar="ARCHIVO.vlf",
        help=("Selecciona un proyecto VLF antes de abrir la GUI, el TUI o ejecutar un comando."),
    )
    commands = parser.add_subparsers(dest="command", metavar="COMANDO")
    register_commands(commands, include_plugin_commands)
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if "--version" in arguments:
        print(f"LANCTL {__version__}")
        raise SystemExit(0)
    if any(value in arguments for value in ("-h", "--help", "/?")):
        return build_parser(include_plugin_commands=False).parse_args(arguments)
    try:
        from app.core.data_migration import ensure_data_layout

        ensure_data_layout()
        run_automatic_log_cleanup()
        from app.i18n import initialize_language, t

        initialize_language()
        from app.assets.icons import initialize_icons

        initialize_icons()
        from app.plugins import get_plugin_manager

        manager = get_plugin_manager()
        plugins_active = not load_plugin_safe_mode() and manager.activate_enabled()
        write_log(f"COMMAND LANCTL {' '.join(arguments)}".rstrip())
        parser = build_parser(include_plugin_commands=True)
        args = parser.parse_args(arguments)
        if plugins_active:
            mode = (
                "tui"
                if args.tui
                else "cli"
                if args.cli
                else "gui"
                if args.gui or not args.command
                else "command"
            )
            manager.events.emit(
                "LANCTL.Core.Lifecycle.Startup",
                {"version": __version__, "mode": mode},
            )
        if args.startup_project:
            from app.projects import activate_project_workspace

            workspace = activate_project_workspace(args.startup_project)
            manager.events.emit(
                "LANCTL.Project.File.Open",
                {
                    "path": str(workspace.project),
                    "project_id": workspace.project_id,
                },
            )
            write_log(f"PROJECT USE id={workspace.project_id} path={workspace.project}")
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
