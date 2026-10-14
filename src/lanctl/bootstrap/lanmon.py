"""Punto de entrada dedicado a monitorización LANCTL."""

from __future__ import annotations

import sys

from lanctl import __version__
from lanctl.apps.monitor.commands import register_monitor_command
from lanctl.bootstrap.lanctl import configure_utf8_stdio
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments
from lanctl.core.session import coordinated_launcher


class _StandaloneCommand:
    def __init__(self, parser: LANCTLArgumentParser) -> None:
        self.parser = parser

    def add_parser(self, _name: str, **_kwargs):
        return self.parser


def build_parser() -> LANCTLArgumentParser:
    parser = LANCTLArgumentParser(
        prog="LANMON",
        description="Monitorización, eventos e incidencias de la suite LANCTL.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión común de la suite y termina.",
    )
    register_monitor_command(_StandaloneCommand(parser))
    for action in parser._actions:
        if action.dest == "words":
            action.help = "logs, events, status, attach, detach, once, session, incidents, service o foreground."
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", "-cli", action="store_true", help="Abre la consola de comandos.")
    mode.add_argument(
        "--tui", "-tui", action="store_true", help="Abre el visor tabular de eventos."
    )
    parser.add_argument(
        "--source", choices=("all", "program", "project"), default="all", help="Origen para logs."
    )
    parser.add_argument("--limit", type=int, default=100, help="Máximo de eventos (1-1000).")
    parser.add_argument(
        "--window",
        action="store_true",
        help="Abre logs en otra terminal y sigue el registro común.",
    )
    parser.add_argument(
        "--level", type=int, default=1, help="Nivel mínimo (1-59); conserva líneas sin nivel."
    )
    return parser


def _main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    if arguments and arguments[0] == "backend":
        from lanctl.core.coordination_cli import run

        return run(arguments[1:])
    args = build_parser().parse_args(arguments or ["status"])
    if args.window and (args.words != ["logs"] or args.cli or args.tui):
        raise ValueError("--window solo se utiliza con logs")
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
    from lanctl.core.errors import errors

    try:
        return _main(argv)
    except (OSError, ValueError) as exc:
        errors.from_exception(
            exc, origin="LANCTL.Monitor.CLI.Command", code="MONITOR.COMMAND.FAILED", level=42
        )
        return 2


__all__ = ["main"]
