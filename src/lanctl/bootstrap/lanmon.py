"""Punto de entrada dedicado a monitorización LANCTL."""

from __future__ import annotations

import sys

from lanctl import __version__
from lanctl.apps.ip.interfaces.cli.commands.monitor import register_monitor_command
from lanctl.apps.ip.interfaces.cli.main import configure_utf8_stdio
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments


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
    return parser


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    args = build_parser().parse_args(arguments or ["status"])
    return args.handler(args)


__all__ = ["main"]
