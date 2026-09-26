"""CLI y TUI de visualización de LANRACK."""

from __future__ import annotations

import json
import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.apps.rack.service import RackService
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> LANCTLArgumentParser:
    parser = LANCTLArgumentParser(prog="LANRACK", description="Visualiza racks y sus equipos.")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Muestra la versión común de la suite y termina.",
    )
    parser.add_argument(
        "--database",
        default=DEFAULT_DATABASE_PATH,
        metavar="ARCHIVO.db",
        help="Base física IDF compartida.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-tui", "--tui", action="store_true", help="Abre la interfaz de pantalla completa."
    )
    mode.add_argument("--cli", "-cli", action="store_true", help="Abre la consola interactiva.")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("list", aliases=["ls"], help="Lista los racks disponibles.")
    show = commands.add_parser("show", help="Muestra un rack y sus ocupantes.")
    show.add_argument("rack", help="ID o nombre del rack.")
    return parser


def _print_rack(rack: dict) -> None:
    print(f"{rack['id']} | {rack['name']} | {rack['units']}U | {len(rack['occupants'])} elementos")
    for item in rack["occupants"]:
        unit = f"U{item['unit']}" if item["unit"] is not None else "U?"
        print(f"  {unit:>4}  {item['id']:<10} {item['name'] or item['type']}")


def run_tui(service: RackService) -> int:
    return _console(service, tui=True)


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    args = build_parser().parse_args(arguments)
    service = RackService(args.database)
    if args.tui or (not args.cli and args.command is None):
        return run_tui(service)
    if args.command in {"list", "ls"}:
        for rack in service.list():
            _print_rack(rack)
        return 0
    if args.command == "show":
        print(json.dumps(service.get(args.rack), indent=2, ensure_ascii=False))
        return 0
    return run_cli(service)


def run_cli(service: RackService) -> int:
    return _console(service)


def _console(service: RackService, *, tui=False) -> int:
    from lanctl.core.interactive_console import command_console

    def dispatch(words):
        args = build_parser().parse_args(words)
        if args.command in {"list", "ls"}:
            for rack in service.list():
                _print_rack(rack)
        elif args.command == "show":
            _print_rack(service.get(args.rack))
        else:
            build_parser().print_help()
        return 0

    def overview():
        rows = service.list()
        inventory = "\n".join(
            f"{row['id']:<12} {row['name']} · {row['units']}U · {len(row['occupants'])} elementos"
            for row in rows
        )
        return (
            (inventory or "No hay racks definidos en LANWIRE.")
            + "\n\nlist: listar · show ID: unidades y ocupantes · R: refrescar\nLa edición física pertenece a LANWIRE."
        )

    return command_console(
        "LANRACK",
        dispatch,
        tui=tui,
        overview=overview,
        shortcuts={"r": ["list"]},
    )
