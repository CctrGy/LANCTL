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
    mode.add_argument("--cli", action="store_true", help="Abre la consola interactiva.")
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
    print("\x1b[2J\x1b[H", end="")
    while True:
        print("\x1b[H", end="")
        print(f"LANRACK TUI {__version__}\n")
        racks = service.list()
        if not racks:
            print("No hay racks definidos en la base física de LANWIRE.")
        for index, rack in enumerate(racks, 1):
            print(
                f"[{index}] {rack['id']:<10} {rack['name']:<24} {rack['units']:>2}U  {len(rack['occupants'])} elementos"
            )
        try:
            choice = input("\nNúmero/ID del rack, R para refrescar o Q para salir: \x1b[J").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if choice.casefold() in {"q", "quit", "exit"}:
            return 0
        if choice.casefold() in {"", "r"}:
            continue
        identifier = (
            racks[int(choice) - 1]["id"]
            if choice.isdigit() and 0 < int(choice) <= len(racks)
            else choice
        )
        try:
            print("\x1b[H", end="")
            _print_rack(service.get(identifier))
        except ValueError as error:
            print(f"Error: {error}")
        input("\nPulsa Intro para volver…\x1b[J")


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
    print(f"LANRACK CLI {__version__} | list, show ID, exit")
    while True:
        try:
            value = input("LANRACK> ").strip().split()
        except (EOFError, KeyboardInterrupt):
            return 0
        if not value:
            continue
        if value[0].casefold() in {"exit", "quit"}:
            return 0
        try:
            if value[0].casefold() in {"list", "ls"}:
                for rack in service.list():
                    _print_rack(rack)
            elif value[0].casefold() == "show" and len(value) == 2:
                _print_rack(service.get(value[1]))
            else:
                print("Usa: list | show ID | exit")
        except ValueError as error:
            print(f"Error: {error}")
