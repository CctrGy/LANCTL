"""Punto de entrada CLI de LANWIRE dentro de la suite LANCTL."""

from __future__ import annotations

import argparse
import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH, IDFDatabaseManager


def configure_utf8_stdio() -> None:
    """Aplica el mismo contrato UTF-8 que la entrada de LANCTL."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="LANWIRE",
        description="Gestión física, IDF, cableado y topología de la suite LANCTL.",
    )
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
        help="Base física IDF; por defecto usa physical/idf.db en la raíz compartida.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "-tui", "--tui", action="store_true", help="Abre la interfaz de pantalla completa."
    )
    mode.add_argument("--cli", action="store_true", help="Abre la consola interactiva de LANWIRE.")

    subcommands = parser.add_subparsers(dest="command", metavar="COMANDO")
    subcommands.add_parser("tui", help="Abre la interfaz de pantalla completa.")
    subcommands.add_parser("cli", help="Abre la consola interactiva.")
    list_command = subcommands.add_parser("list", aliases=["ls"], help="Lista los identificadores.")
    list_command.add_argument("prefix", nargs="?")
    subcommands.add_parser("seed", help="Carga la topología inicial de pruebas.")
    show = subcommands.add_parser("show", help="Muestra un identificador.")
    show.add_argument("idf")
    add = subcommands.add_parser("add", help="Genera el siguiente IDF.")
    add.add_argument("prefix")
    add.add_argument("data", nargs="*", metavar="CLAVE=VALOR")
    reserve = subcommands.add_parser("reserve", help="Reserva un IDF.")
    reserve.add_argument("idf")
    reserve.add_argument("data", nargs="*", metavar="CLAVE=VALOR")
    delete = subcommands.add_parser("delete", aliases=["del"], help="Elimina un IDF.")
    delete.add_argument("idf")
    prefix = subcommands.add_parser("prefix", help="Gestiona juegos de letras.")
    prefix_commands = prefix.add_subparsers(dest="prefix_action", required=True)
    prefix_commands.add_parser("list", aliases=["ls"], help="Lista las definiciones.")
    prefix_show = prefix_commands.add_parser("show", help="Muestra una definición.")
    prefix_show.add_argument("letters")
    prefix_set = prefix_commands.add_parser("set", help="Crea o actualiza una definición.")
    prefix_set.add_argument("letters")
    prefix_set.add_argument("name")
    prefix_set.add_argument("description", nargs="?", default="")
    prefix_delete = prefix_commands.add_parser(
        "delete", aliases=["del"], help="Elimina una definición."
    )
    prefix_delete.add_argument("letters")
    return parser


def run_cli(database_path: str) -> int:
    """Consola persistente equivalente al modo CLI de LANCTL."""
    processor = CommandProcessor(IDFDatabaseManager(database_path))
    print(f"LANWIRE CLI {__version__}")
    print("Escribe 'help' para listar comandos y 'exit' para salir.")
    while True:
        try:
            command = input("LANWIRE> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        result = processor.execute(command)
        for line in result.lines:
            print(line)
        if result.exit_requested:
            return 0


def _command_parts(args: argparse.Namespace) -> list[str]:
    command = (
        "list" if args.command == "ls" else "delete" if args.command == "del" else args.command
    )
    parts = [command]
    if command == "prefix":
        action = (
            "list"
            if args.prefix_action == "ls"
            else "delete"
            if args.prefix_action == "del"
            else args.prefix_action
        )
        parts.append(action)
        if hasattr(args, "letters"):
            parts.append(args.letters)
        if hasattr(args, "name"):
            parts.append(f'"{args.name}"')
        if getattr(args, "description", ""):
            parts.append(f'"{args.description}"')
    elif command == "list" and args.prefix:
        parts.append(args.prefix)
    if hasattr(args, "idf"):
        parts.append(args.idf)
    if command == "add":
        parts.append(args.prefix)
    parts.extend(getattr(args, "data", []))
    return parts


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = list(sys.argv[1:] if argv is None else argv)
    arguments = ["--help" if value == "/?" else value for value in arguments]
    args = build_parser().parse_args(arguments)
    if args.tui or args.command == "tui" or (not args.cli and args.command is None):
        from lanctl.apps.wire.tui import run_tui

        return run_tui(args.database)
    if args.cli or args.command == "cli":
        return run_cli(args.database)

    processor = CommandProcessor(IDFDatabaseManager(args.database))
    result = processor.execute(" ".join(_command_parts(args)))
    for line in result.lines:
        print(line)
    return 1 if result.lines and result.lines[0].startswith("Error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
