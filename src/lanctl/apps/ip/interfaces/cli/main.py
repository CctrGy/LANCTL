from __future__ import annotations

import argparse
import io
import sys
import time
from contextlib import redirect_stdout, suppress
from contextvars import ContextVar
from importlib import import_module

from lanctl import __version__
from lanctl.core.errors import LanctlError
from lanctl.core.log_cleanup import run_automatic_log_cleanup
from lanctl.core.logger import write_log

# El registro usa nombres importables para que `lanctl --version` no cargue
# drivers de red, GUI, SSH y plugins antes de saber qué modo se ha solicitado.
_COMMAND_REGISTRARS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("lanctl.apps.ip.interfaces.cli.commands.list", ("register_list_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.recurrent", ("register_recurrent_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.ping", ("register_ping_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.open", ("register_open_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.settings", ("register_settings_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.call", ("register_call_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.search", ("register_search_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.scan", ("register_scan_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.cnf", ("register_cnf_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.credential", ("register_credential_command",)),
    (
        "lanctl.apps.ip.interfaces.cli.commands.download_settings",
        ("register_gateway_command", "register_download_settings_command"),
    ),
    ("lanctl.apps.ip.interfaces.cli.commands.protocol", ("register_protocol_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.ssh", ("register_ssh_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.radmin", ("register_radmin_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.wol", ("register_wol_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.history", ("register_history_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.monitor", ("register_monitor_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.access", ("register_access_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.smb", ("register_smb_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.terminal", ("register_terminal_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.switch", ("register_switch_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.group", ("register_group_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.element", ("register_element_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.name", ("register_name_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.alias", ("register_alias_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.project", ("register_project_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.plugin", ("register_plugin_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.language", ("register_language_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.error", ("register_error_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.database", ("register_database_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.demo", ("register_demo_command",)),
    ("lanctl.apps.ip.interfaces.cli.commands.lanwire", ("register_lanwire_command",)),
)
_MAIN_DEPTH: ContextVar[int] = ContextVar("lanctl_main_depth", default=0)


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
        from lanctl.core.plugins.declarative_commands import register_declarative_commands

        register_declarative_commands(commands)


def run_global_cli() -> int:
    """Carga la consola persistente únicamente cuando se solicita ``--cli``."""

    from lanctl.apps.ip.interfaces.cli.commands.modes import run_global_cli as run

    return run()


def print_error(message: str) -> None:
    """Evita cargar Colorama durante rutas rápidas como ``--version``."""

    from lanctl.core.console import error

    error(message)


def build_parser(include_plugin_commands: bool = False) -> argparse.ArgumentParser:
    from lanctl.core.parser import LANCTLArgumentParser
    from lanctl.shared.i18n import t

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
    detail = parser.add_mutually_exclusive_group()
    detail.add_argument(
        "--quiet", action="store_true", help="Omite la salida correcta; conserva errores."
    )
    detail.add_argument(
        "--verbose", action="store_true", help="Añade diagnóstico de ejecución a stderr."
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
        nargs="?",
        const="inventory",
        default=None,
        type=str.casefold,
        choices=("inventory", "plugins", "projects", "settings"),
        metavar="VENTANA",
        help=(
            f"{t('LANCTL.CORE.APP.TUI_HELP')} "
            "Puede abrir directamente PLUGINS, PROJECTS o SETTINGS."
        ),
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
    if arguments == ["--version"]:
        print(f"LANCTL {__version__}")
        raise SystemExit(0)
    if any(value in arguments for value in ("-h", "--help", "/?")):
        return build_parser(include_plugin_commands=False).parse_args(arguments)
    depth = _MAIN_DEPTH.get()
    depth_token = _MAIN_DEPTH.set(depth + 1)
    autosave_scheduler = None
    try:
        from lanctl.core.data_migration import ensure_data_layout

        ensure_data_layout()
        run_automatic_log_cleanup()
        from lanctl.shared.i18n import initialize_language, t

        initialize_language()
        from lanctl.shared.assets.icons import initialize_icons

        initialize_icons()
        from lanctl.core.plugins import get_plugin_manager

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
            from lanctl.core.projects import activate_project_workspace

            workspace = activate_project_workspace(args.startup_project)
            manager.events.emit(
                "LANCTL.Project.File.Open",
                {
                    "path": str(workspace.project),
                    "project_id": workspace.project_id,
                },
            )
            write_log(f"PROJECT USE id={workspace.project_id} path={workspace.project}")
        if depth == 0:
            from lanctl.core.projects.save_policy import start_autosave_scheduler

            autosave_scheduler = start_autosave_scheduler()
        if args.gui or (not args.command and not args.tui and not args.cli):
            from lanctl.apps.ip.interfaces.gui.main import run_gui

            return run_gui()
        if args.tui:
            from lanctl.apps.ip.interfaces.tui.main import run_tui

            return run_tui(None if args.tui == "inventory" else args.tui)
        if args.cli:
            return run_global_cli()
        result = _run_handler(args)
        from lanctl.core.projects.save_policy import SaveTrigger, save_active_project

        save_active_project(SaveTrigger.CHANGE)
        return result
    except KeyboardInterrupt:
        print_error(t("LANCTL.CORE.APP.CANCELLED"))
        return 130
    except LanctlError as error:
        if error.print_output:
            print_error(repr(error))
        return error.exit_code
    except (OSError, RuntimeError, ValueError) as error:
        from lanctl.core.errors import errors

        event = errors.from_exception(
            error,
            origin="LANCTL.Core.CLI.Command",
            code=f"CLI.{type(error).__name__.upper()}",
            level=46
            if isinstance(error, OSError)
            else 43
            if isinstance(error, RuntimeError)
            else 34,
            print_output=False,
        )
        print_error(repr(event))
        return 2
    finally:
        _MAIN_DEPTH.reset(depth_token)
        if depth == 0:
            try:
                if autosave_scheduler is not None:
                    autosave_scheduler.stop()
                from lanctl.core.projects.save_policy import close_active_project

                close_active_project()
            except Exception as error:  # noqa: BLE001 - el cierre no debe ocultar el resultado
                write_log(f"PROJECT AUTOSAVE CLOSE ERROR detail={error}")


def load_plugin_safe_mode() -> bool:
    from lanctl.core.config import load_config

    return bool(load_config().get("pluginSafeMode", False))


def _run_handler(args: argparse.Namespace) -> int:
    """Aplica quiet/verbose sin obligar a cada comando a duplicar la política."""

    quiet = bool(getattr(args, "quiet", False))
    verbose = bool(getattr(args, "verbose", False))
    started = time.perf_counter()
    command = str(getattr(args, "command", "") or "-")
    if verbose:
        print(f"LANCTL diagnostic: command={command} phase=start", file=sys.stderr)
    if quiet:
        with redirect_stdout(io.StringIO()):
            result = args.handler(args)
    else:
        result = args.handler(args)
    code = int(result or 0)
    if verbose:
        elapsed = time.perf_counter() - started
        print(
            f"LANCTL diagnostic: command={command} phase=end code={code} elapsed={elapsed:.3f}s",
            file=sys.stderr,
        )
    return code
