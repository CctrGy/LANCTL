"""Punto de entrada dedicado a monitorización LANCTL."""

from __future__ import annotations

import sys

from lanctl import __version__
from lanctl.apps.monitor.commands import register_monitor_command
from lanctl.bootstrap.lanctl import configure_utf8_stdio
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments
from lanctl.core.session import coordinated_launcher
from lanctl.shared.i18n import initialize_language, t


class _StandaloneCommand:
    def __init__(self, parser: LANCTLArgumentParser) -> None:
        self.parser = parser

    def add_parser(self, _name: str, **_kwargs):
        return self.parser


def build_parser() -> LANCTLArgumentParser:
    parser = LANCTLArgumentParser(
        prog="LANMON",
        description=t("LANCTL.UI.TEXT.MONITORING_EVENTS_AND_INCIDENTS_FOR_THE_LANCTL_SUITE"),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help=t("LANCTL.UI.TEXT.SHOW_THE_COMMON_SUITE_VERSION_AND_EXIT"),
    )
    register_monitor_command(_StandaloneCommand(parser))
    for action in parser._actions:
        if action.dest == "words":
            action.help = "logs, events, status, attach, detach, once, session, incidents, service o foreground."
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--gui", action="store_true", help=t("LANCTL.UI.TEXT.OPEN_THE_DESKTOP_GRAPHICAL_INTERFACE")
    )
    mode.add_argument(
        "--cli", "-cli", action="store_true", help=t("LANCTL.UI.TEXT.OPEN_THE_COMMAND_CONSOLE")
    )
    mode.add_argument(
        "--tui", "-tui", action="store_true", help=t("LANCTL.UI.TEXT.OPEN_THE_TABULAR_EVENT_VIEWER")
    )
    parser.add_argument(
        "--source",
        choices=("all", "program", "project"),
        default="all",
        help=t("LANCTL.UI.TEXT.LOG_SOURCE"),
    )
    parser.add_argument(
        "--limit", type=int, default=100, help=t("LANCTL.UI.TEXT.MAXIMUM_NUMBER_OF_EVENTS_1_1000")
    )
    parser.add_argument(
        "--window",
        action="store_true",
        help=t("LANCTL.UI.TEXT.OPEN_LOGS_IN_ANOTHER_TERMINAL_AND_FOLLOW_THE_COMMON_LOG"),
    )
    parser.add_argument(
        "--level",
        type=int,
        default=1,
        help=t("LANCTL.UI.TEXT.MINIMUM_LEVEL_1_59_PRESERVE_LINES_WITHOUT_A_LEVEL"),
    )
    return parser


def _main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    if arguments and arguments[0] == "backend":
        from lanctl.core.coordination_cli import run

        return run(arguments[1:])
    args = build_parser().parse_args(arguments or ["status"])
    if getattr(args, "gui", False):
        from lanctl.apps.suite.launcher_gui import run_gui

        return run_gui("lanmon", project=args.project)
    if args.window and (args.words != ["logs"] or args.cli):
        raise ValueError("--window solo se utiliza con logs")
    if args.words == ["logs"] and args.tui and not args.cli:
        from lanctl.apps.monitor.log_stream import open_log_window
        from lanctl.apps.monitor.log_tui import follow_log_tui

        if args.project or args.source == "project":
            raise ValueError("La TUI en directo muestra el log operativo, no auditorías VLF.")
        if args.window:
            return open_log_window(limit=args.limit, minimum=args.level, tui=True)
        return follow_log_tui(limit=args.limit, minimum=args.level)
    if args.cli or args.tui:
        from lanctl.core.interactive_console import command_console

        prefix = ["--project", args.project] if args.project else []
        return command_console(
            "LANMON",
            lambda words: main([*prefix, *words]),
            tui=args.tui,
            overview=(
                "logs: registros de programa y proyecto\n"
                "events: eventos del monitor · status: estado\n"
                "incidents: incidencias · service: gestión de servicio\n"
                "backend sessions / events / tasks: coordinación entre launchers\n"
                "help: todas las opciones. Ningún servicio se inicia al abrir este panel."
            ),
        )
    if args.words == ["logs"]:
        if args.follow or args.window:
            from lanctl.apps.monitor.log_stream import follow_logs, open_log_window

            if args.project or args.source == "project":
                raise ValueError(
                    "El seguimiento muestra el log común del programa, no el archivo VLF."
                )
            action = open_log_window if args.window else follow_logs
            return action(limit=args.limit, minimum=args.level)
        import json

        from lanctl.apps.monitor.event_view import read_events
        from lanctl.core.config import load_config

        print(
            json.dumps(
                read_events(
                    load_config(),
                    project=args.project,
                    source=args.source,
                    limit=args.limit,
                    minimum=args.level,
                ),
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0
    return args.handler(args)


@coordinated_launcher("lanmon")
def main(argv: list[str] | None = None) -> int:
    initialize_language()
    from lanctl.core.errors import errors

    try:
        return _main(argv)
    except (OSError, ValueError) as exc:
        errors.from_exception(
            exc, origin="LANCTL.Monitor.CLI.Command", code="MONITOR.COMMAND.FAILED", level=42
        )
        return 2


__all__ = ["main"]
