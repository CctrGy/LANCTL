"""Punto de entrada CLI de LANWIRE dentro de la suite LANCTL."""

from __future__ import annotations

import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH, IDFDatabaseManager
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments


def configure_utf8_stdio() -> None:
    """Aplica el mismo contrato UTF-8 que la entrada de LANCTL."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> LANCTLArgumentParser:
    parser = LANCTLArgumentParser(
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
    subcommands.add_parser("help", help="Muestra la ayuda de comandos de LANWIRE.")
    list_command = subcommands.add_parser("list", aliases=["ls"], help="Lista los identificadores.")
    list_command.add_argument("prefix", nargs="?", help="Filtra por prefijo IDF.")
    subcommands.add_parser("seed", help="Carga la topología inicial de pruebas.")
    show = subcommands.add_parser("show", help="Muestra un identificador.")
    show.add_argument("idf", help="Identificador físico que se desea consultar.")
    add = subcommands.add_parser("add", help="Genera el siguiente IDF.")
    add.add_argument("prefix", help="Prefijo del tipo de elemento físico.")
    add.add_argument(
        "--digits", type=int, choices=range(2, 6), help="Cantidad de dígitos del contador (2 a 5)."
    )
    add.add_argument(
        "-more", "--more", type=int, default=1, metavar="N", help="Crea N IDF consecutivos."
    )
    idf = subcommands.add_parser("idf", help="Crea identificadores con perfil físico completo.")
    idf_actions = idf.add_subparsers(dest="idf_action", required=True)
    idf_list = idf_actions.add_parser("list", help="Lista prefijos o los IDF de uno de ellos.")
    idf_list.add_argument("prefix", nargs="?", help="Prefijo cuyos elementos se listan.")
    idf_actions.add_parser("types", help="Lista los perfiles físicos disponibles.")
    idf_show = idf_actions.add_parser("show", help="Consulta un prefijo o IDF.")
    idf_show.add_argument("code", help="Prefijo o IDF concreto.")
    idf_edit = idf_actions.add_parser("edit", help="Edita un prefijo o los datos de un IDF.")
    idf_edit.add_argument("code", help="Prefijo o IDF concreto.")
    idf_edit.add_argument("data", nargs="*", metavar="CAMPO=VALOR", help="Datos del IDF.")
    idf_edit.add_argument(
        "-type", dest="element_type", default="", help="Nuevo perfil del prefijo."
    )
    idf_edit.add_argument("-name", default="", help="Nombre del prefijo.")
    idf_edit.add_argument("-alias", default="", help="Alias del prefijo.")
    idf_edit.add_argument("-description", default="", help="Descripción del prefijo.")
    idf_delete = idf_actions.add_parser("delete", aliases=["del"], help="Elimina un IDF.")
    idf_delete.add_argument("code", help="IDF concreto; no elimina prefijos.")
    idf_new = idf_actions.add_parser("new", help="Asigna un perfil físico a un prefijo.")
    idf_add = idf_actions.add_parser("add", help="Crea un IDF del perfil asignado al prefijo.")
    for action_parser in (idf_new, idf_add):
        action_parser.add_argument("code", help="Prefijo para new o IDF exacto para add.")
        action_parser.add_argument("-name", default="", help="Nombre del registro.")
        action_parser.add_argument("-alias", default="", help="Alias opcional.")
        action_parser.add_argument(
            "-description", "-descriptionn", default="", help="Descripción opcional."
        )
    idf_new.add_argument("-type", required=True, dest="element_type", help="Perfil físico.")
    reserve = subcommands.add_parser("reserve", help="Reserva un IDF.")
    reserve.add_argument("idf", help="IDF exacto que se desea reservar.")
    reserve.add_argument(
        "data", nargs="*", metavar="CLAVE=VALOR", help="Datos iniciales opcionales."
    )
    element = subcommands.add_parser(
        "element", help="Consulta o actualiza los datos y puertos de un elemento."
    )
    element.add_argument("idf", help="IDF que se desea consultar o actualizar.")
    element.add_argument(
        "data", nargs="*", metavar="CAMPO=VALOR", help="Campos físicos que se desean modificar."
    )
    delete = subcommands.add_parser("delete", aliases=["del"], help="Elimina un IDF.")
    delete.add_argument("idf", help="IDF que se desea eliminar.")
    subcommands.add_parser("graph", aliases=["map"], help="Muestra la topología física.")
    prefix = subcommands.add_parser("prefix", help="Gestiona juegos de letras.")
    prefix_commands = prefix.add_subparsers(dest="prefix_action", required=True)
    prefix_commands.add_parser("list", aliases=["ls"], help="Lista las definiciones.")
    prefix_show = prefix_commands.add_parser("show", help="Muestra una definición.")
    prefix_show.add_argument("letters", help="Letras del prefijo.")
    prefix_set = prefix_commands.add_parser("set", help="Crea o actualiza una definición.")
    prefix_set.add_argument("letters", help="Letras del prefijo.")
    prefix_set.add_argument("name", help="Nombre descriptivo del tipo.")
    prefix_set.add_argument("description", nargs="?", default="", help="Descripción opcional.")
    prefix_delete = prefix_commands.add_parser(
        "delete", aliases=["del"], help="Elimina una definición."
    )
    prefix_delete.add_argument("letters", help="Letras del prefijo que se desea eliminar.")
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


def _command_parts(args) -> list[str]:
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
            parts.append(args.name)
        if getattr(args, "description", ""):
            parts.append(args.description)
    elif command == "list" and args.prefix:
        parts.append(args.prefix)
    if hasattr(args, "idf"):
        parts.append(args.idf)
    if command == "add":
        parts.append(args.prefix)
        if args.digits is not None:
            parts.extend(("--digits", str(args.digits)))
        if args.more != 1:
            parts.extend(("-more", str(args.more)))
    if command == "idf":
        parts.append("delete" if args.idf_action == "del" else args.idf_action)
        if args.idf_action == "list":
            if args.prefix:
                parts.append(args.prefix)
            return parts
        if args.idf_action == "types":
            return parts
        parts.append(args.code)
        if args.idf_action == "edit" and "-" in args.code:
            parts.extend(args.data)
            return parts
        if getattr(args, "element_type", ""):
            parts.extend(("-type", args.element_type))
        if getattr(args, "name", ""):
            parts.extend(("-name", args.name))
        if getattr(args, "alias", ""):
            parts.extend(("-alias", args.alias))
        if getattr(args, "description", ""):
            parts.extend(("-description", args.description))
    if command == "reserve":
        parts.extend(args.data)
    if command == "element":
        parts.extend(args.data)
    return parts


def main(argv: list[str] | None = None) -> int:
    configure_utf8_stdio()
    arguments = list(sys.argv[1:] if argv is None else argv)
    arguments = normalize_help_arguments(arguments)
    args = build_parser().parse_args(arguments)
    if args.tui or args.command == "tui" or (not args.cli and args.command is None):
        from lanctl.apps.wire.tui import run_tui

        return run_tui(args.database)
    if args.cli or args.command == "cli":
        return run_cli(args.database)

    processor = CommandProcessor(IDFDatabaseManager(args.database))
    result = processor.execute_parts(_command_parts(args))
    for line in result.lines:
        print(line)
    return 1 if result.lines and result.lines[0].startswith("Error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
