"""Orquestador principal de las aplicaciones de la suite."""

from __future__ import annotations

import argparse
import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.core.parser import (
    LANCTLArgumentParser,
    has_help_argument,
    normalize_help_arguments,
)

_LAUNCHERS = {
    "lanip": ("ip", "Inventario lógico, descubrimiento, IP, MAC y servicios."),
    "lanwire": ("wire", "Cableado, puertos, paneles y topología física."),
    "lanrack": ("rack", "Salas técnicas, racks, unidades U y equipos."),
    "lanaccess": ("access", "Usuarios, credenciales y accesos remotos."),
    "lanmon": ("monitor", "Monitorización, eventos, incidencias e historial."),
}


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> LANCTLArgumentParser:
    parser = LANCTLArgumentParser(
        prog="LANCTL",
        description="Orquestador raíz de las aplicaciones de la suite LANCTL.",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}",
        help="Muestra la versión común de la suite y termina.",
    )
    parser.add_argument("--cli", action="store_true", help="Abre la consola principal.")
    parser.add_argument("-tui", "--tui", action="store_true", help="Abre el TUI principal.")
    launchers = parser.add_subparsers(dest="launcher", metavar="LAUNCHER")
    for name, (alias, description) in _LAUNCHERS.items():
        child = launchers.add_parser(name, aliases=[alias], help=description, add_help=False)
        child.add_argument("arguments", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    return parser


def _run_launcher(name: str, arguments: list[str]) -> int:
    canonical = (
        "lanmon"
        if name == "monitor"
        else f"lan{name}"
        if name in {"ip", "wire", "rack", "access"}
        else name
    )
    if canonical == "lanip":
        from lanctl.bootstrap.lanip import main as application
    elif canonical == "lanwire":
        from lanctl.apps.wire.cli.main import main as application
    elif canonical == "lanrack":
        from lanctl.apps.rack.cli import main as application
    elif canonical == "lanaccess":
        from lanctl.apps.access.manager_cli import main as application
    else:
        from lanctl.bootstrap.lanmon import main as application
    return application(arguments)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    launcher_names = {*_LAUNCHERS, "ip", "wire", "rack", "access", "monitor"}
    if has_help_argument(arguments):
        if arguments and arguments[0].casefold() in launcher_names:
            return _run_launcher(arguments[0].casefold(), arguments[1:])
        return build_parser().parse_args(arguments)
    if arguments and arguments[0].casefold() in launcher_names:
        return _run_launcher(arguments[0].casefold(), arguments[1:])
    if not arguments or arguments[0] in {"--cli", "--tui", "-tui"}:
        from lanctl.bootstrap.lanip import main as ip_main

        return ip_main(arguments)
    return build_parser().parse_args(arguments)
