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
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión común de la suite y termina.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", "-cli", action="store_true", help="Abre la consola principal.")
    mode.add_argument("-tui", "--tui", action="store_true", help="Abre el TUI principal.")
    parser.add_argument(
        "--admin",
        action="store_true",
        help="Solicita UAC explícitamente para un launcher instalado en Windows.",
    )
    launchers = parser.add_subparsers(dest="launcher", metavar="LAUNCHER")
    for name, (alias, description) in _LAUNCHERS.items():
        child = launchers.add_parser(name, aliases=[alias], help=description, add_help=False)
        child.add_argument("arguments", nargs=argparse.REMAINDER, help=argparse.SUPPRESS)
    for name in ("plugin", "settings", "language"):
        child = launchers.add_parser(
            name, help="Administración compartida de la suite.", add_help=False
        )
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
    if arguments and arguments[0] == "--admin" and not has_help_argument(arguments):
        from lanctl.core.errors import errors
        from lanctl.core.local_permissions import launch_elevated

        try:
            return launch_elevated(arguments[1:])
        except OSError as exc:
            errors.from_exception(
                exc, origin="LANCTL.Suite.Access.Elevate", code="SUITE.ELEVATION.DENIED", level=46
            )
            return 2
    if arguments and arguments[0] in {"plugin", "settings", "language"}:
        # Compatibility adapter; shared services remain the single source of state.
        from lanctl.bootstrap.lanip import main as ip_main

        return ip_main(arguments)
    launcher_names = {*_LAUNCHERS, "ip", "wire", "rack", "access", "monitor"}
    if has_help_argument(arguments):
        if arguments and arguments[0].casefold() in launcher_names:
            return _run_launcher(arguments[0].casefold(), arguments[1:])
        return build_parser().parse_args(arguments)
    if arguments and arguments[0].casefold() in launcher_names:
        return _run_launcher(arguments[0].casefold(), arguments[1:])
    if not arguments or arguments[0] in {"--cli", "-cli", "--tui", "-tui"}:
        from lanctl.apps.suite.interfaces import run_console

        args = build_parser().parse_args(arguments)
        if args.launcher:
            build_parser().error("usa lanctl LAUNCHER --cli o --tui")
        return run_console(tui=args.tui)
    parser = build_parser()
    parser.parse_args(arguments)
    parser.error("indica un launcher o utiliza --cli / --tui")
