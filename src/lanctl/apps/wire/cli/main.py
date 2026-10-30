"""Punto de entrada CLI de LANWIRE dentro de la suite LANCTL."""

from __future__ import annotations

import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH, IDFDatabaseManager
from lanctl.core.config import load_config
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments
from lanctl.core.projects.console_session import physical_console_session
from lanctl.core.session import coordinated_launcher
from lanctl.shared.i18n import initialize_language, t


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
        description=t(
            "LANCTL.UI.TEXT.PHYSICAL_MANAGEMENT_IDF_WIRING_AND_TOPOLOGY_FOR_THE_LANCTL_SUITE"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help=t("LANCTL.UI.TEXT.SHOW_THE_COMMON_SUITE_VERSION_AND_EXIT"),
    )
    parser.add_argument(
        "--database",
        default=load_config().get("physicalDatabase", DEFAULT_DATABASE_PATH),
        metavar="ARCHIVO.db",
        help=t(
            "LANCTL.UI.TEXT.PHYSICAL_IDF_DATABASE_DEFAULTS_TO_PHYSICAL_IDF_DB_IN_THE_SHARED_ROOT"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--gui", action="store_true", help=t("LANCTL.UI.TEXT.OPEN_THE_DESKTOP_GRAPHICAL_INTERFACE")
    )
    mode.add_argument(
        "-tui",
        "--tui",
        action="store_true",
        help=t("LANCTL.UI.TEXT.OPEN_THE_FULL_SCREEN_INTERFACE"),
    )
    mode.add_argument(
        "--cli",
        "-cli",
        action="store_true",
        help=t("LANCTL.UI.TEXT.OPEN_THE_LANWIRE_INTERACTIVE_CONSOLE"),
    )

    subcommands = parser.add_subparsers(dest="command", metavar="COMANDO")
    subcommands.add_parser("tui", help=t("LANCTL.UI.TEXT.OPEN_THE_FULL_SCREEN_INTERFACE"))
    subcommands.add_parser("cli", help=t("LANCTL.UI.TEXT.OPEN_THE_INTERACTIVE_CONSOLE"))
    subcommands.add_parser("help", help=t("LANCTL.UI.TEXT.SHOW_LANWIRE_COMMAND_HELP"))
    list_command = subcommands.add_parser(
        "list", aliases=["ls"], help=t("LANCTL.UI.TEXT.LIST_IDENTIFIERS")
    )
    list_command.add_argument("prefix", nargs="?", help=t("LANCTL.UI.TEXT.FILTER_BY_IDF_PREFIX"))
    subcommands.add_parser("seed", help=t("LANCTL.UI.TEXT.LOAD_THE_INITIAL_TEST_TOPOLOGY"))
    show = subcommands.add_parser("show", help=t("LANCTL.UI.TEXT.SHOW_AN_IDENTIFIER"))
    show.add_argument("idf", help=t("LANCTL.UI.TEXT.PHYSICAL_IDENTIFIER_TO_QUERY"))
    add = subcommands.add_parser("add", help=t("LANCTL.UI.TEXT.GENERATE_THE_NEXT_IDF"))
    add.add_argument("prefix", help=t("LANCTL.UI.TEXT.PHYSICAL_ELEMENT_TYPE_PREFIX"))
    add.add_argument(
        "--digits",
        type=int,
        choices=range(2, 6),
        help=t("LANCTL.UI.TEXT.NUMBER_OF_COUNTER_DIGITS_2_TO_5"),
    )
    add.add_argument(
        "-more",
        "--more",
        type=int,
        default=1,
        metavar="N",
        help=t("LANCTL.UI.TEXT.CREATE_N_CONSECUTIVE_IDFS"),
    )
    idf = subcommands.add_parser(
        "idf", help=t("LANCTL.UI.TEXT.CREATE_IDENTIFIERS_WITH_A_COMPLETE_PHYSICAL_PROFILE")
    )
    idf_actions = idf.add_subparsers(dest="idf_action", required=True)
    idf_list = idf_actions.add_parser(
        "list", help=t("LANCTL.UI.TEXT.LIST_PREFIXES_OR_THE_IDFS_OF_A_PREFIX")
    )
    idf_list.add_argument(
        "prefix", nargs="?", help=t("LANCTL.UI.TEXT.PREFIX_WHOSE_ELEMENTS_ARE_LISTED")
    )
    idf_actions.add_parser("types", help=t("LANCTL.UI.TEXT.LIST_AVAILABLE_PHYSICAL_PROFILES"))
    idf_show = idf_actions.add_parser("show", help=t("LANCTL.UI.TEXT.QUERY_A_PREFIX_OR_IDF"))
    idf_show.add_argument("code", help=t("LANCTL.UI.TEXT.SPECIFIC_PREFIX_OR_IDF"))
    idf_edit = idf_actions.add_parser("edit", help=t("LANCTL.UI.TEXT.EDIT_A_PREFIX_OR_IDF_DATA"))
    idf_edit.add_argument("code", help=t("LANCTL.UI.TEXT.SPECIFIC_PREFIX_OR_IDF"))
    idf_edit.add_argument(
        "data", nargs="*", metavar="CAMPO=VALOR", help=t("LANCTL.UI.TEXT.IDF_DATA")
    )
    idf_edit.add_argument(
        "-type", dest="element_type", default="", help=t("LANCTL.UI.TEXT.NEW_PREFIX_PROFILE")
    )
    idf_edit.add_argument("-name", default="", help=t("LANCTL.UI.TEXT.PREFIX_NAME"))
    idf_edit.add_argument("-alias", default="", help=t("LANCTL.UI.TEXT.PREFIX_ALIAS"))
    idf_edit.add_argument("-description", default="", help=t("LANCTL.UI.TEXT.PREFIX_DESCRIPTION"))
    idf_delete = idf_actions.add_parser(
        "delete", aliases=["del"], help=t("LANCTL.UI.TEXT.DELETE_AN_IDF")
    )
    idf_delete.add_argument("code", help=t("LANCTL.UI.TEXT.SPECIFIC_IDF_DOES_NOT_DELETE_PREFIXES"))
    idf_new = idf_actions.add_parser(
        "new", help=t("LANCTL.UI.TEXT.ASSIGN_A_PHYSICAL_PROFILE_TO_A_PREFIX")
    )
    idf_add = idf_actions.add_parser(
        "add", help=t("LANCTL.UI.TEXT.CREATE_AN_IDF_USING_THE_ASSIGNED_PREFIX_PROFILE")
    )
    for action_parser in (idf_new, idf_add):
        action_parser.add_argument(
            "code", help=t("LANCTL.UI.TEXT.PREFIX_FOR_NEW_OR_EXACT_IDF_FOR_ADD")
        )
        action_parser.add_argument("-name", default="", help=t("LANCTL.UI.TEXT.RECORD_NAME"))
        action_parser.add_argument("-alias", default="", help=t("LANCTL.UI.TEXT.OPTIONAL_ALIAS"))
        action_parser.add_argument(
            "-description",
            "-descriptionn",
            default="",
            help=t("LANCTL.UI.TEXT.OPTIONAL_DESCRIPTION"),
        )
    idf_new.add_argument(
        "-type", required=True, dest="element_type", help=t("LANCTL.UI.TEXT.PHYSICAL_PROFILE")
    )
    reserve = subcommands.add_parser("reserve", help=t("LANCTL.UI.TEXT.RESERVE_AN_IDF"))
    reserve.add_argument("idf", help=t("LANCTL.UI.TEXT.EXACT_IDF_TO_RESERVE"))
    reserve.add_argument(
        "data", nargs="*", metavar="CLAVE=VALOR", help=t("LANCTL.UI.TEXT.OPTIONAL_INITIAL_DATA")
    )
    element = subcommands.add_parser(
        "element", help=t("LANCTL.UI.TEXT.QUERY_OR_UPDATE_AN_ELEMENT_S_DATA_AND_PORTS")
    )
    element.add_argument("idf", help=t("LANCTL.UI.TEXT.IDF_TO_QUERY_OR_UPDATE"))
    element.add_argument(
        "data", nargs="*", metavar="CAMPO=VALOR", help=t("LANCTL.UI.TEXT.PHYSICAL_FIELDS_TO_MODIFY")
    )
    delete = subcommands.add_parser(
        "delete", aliases=["del"], help=t("LANCTL.UI.TEXT.DELETE_AN_IDF")
    )
    delete.add_argument("idf", help=t("LANCTL.UI.TEXT.IDF_TO_DELETE"))
    subcommands.add_parser(
        "graph", aliases=["map"], help=t("LANCTL.UI.TEXT.SHOW_THE_PHYSICAL_TOPOLOGY")
    )
    prefix = subcommands.add_parser("prefix", help=t("LANCTL.UI.TEXT.MANAGE_LETTER_SETS"))
    prefix_commands = prefix.add_subparsers(dest="prefix_action", required=True)
    prefix_commands.add_parser("list", aliases=["ls"], help=t("LANCTL.UI.TEXT.LIST_DEFINITIONS"))
    prefix_show = prefix_commands.add_parser("show", help=t("LANCTL.UI.TEXT.SHOW_A_DEFINITION"))
    prefix_show.add_argument("letters", help=t("LANCTL.UI.TEXT.PREFIX_LETTERS"))
    prefix_set = prefix_commands.add_parser(
        "set", help=t("LANCTL.UI.TEXT.CREATE_OR_UPDATE_A_DEFINITION")
    )
    prefix_set.add_argument("letters", help=t("LANCTL.UI.TEXT.PREFIX_LETTERS"))
    prefix_set.add_argument("name", help=t("LANCTL.UI.TEXT.DESCRIPTIVE_TYPE_NAME"))
    prefix_set.add_argument(
        "description", nargs="?", default="", help=t("LANCTL.UI.TEXT.OPTIONAL_DESCRIPTION")
    )
    prefix_delete = prefix_commands.add_parser(
        "delete", aliases=["del"], help=t("LANCTL.UI.TEXT.DELETE_A_DEFINITION")
    )
    prefix_delete.add_argument("letters", help=t("LANCTL.UI.TEXT.PREFIX_LETTERS_TO_DELETE"))
    return parser


def run_cli(database_path: str) -> int:
    """Consola persistente equivalente al modo CLI de LANCTL."""
    with physical_console_session(database_path) as session:
        session.start()
        return _console(session)


def _console(session):
    processor = None
    print(f"LANWIRE CLI {__version__}")
    print(t("LANCTL.WIRE.CONSOLE.INTRO"))
    while True:
        with session.operation():
            pass
        for message in session.messages():
            print(message)
        try:
            command = input("LANWIRE> ")
        except (EOFError, KeyboardInterrupt):
            print()
            return 0 if session.request_close(interactive=False) else 1
        with session.operation() as path:
            if processor is None or processor.database.path.resolve() != path:
                processor = CommandProcessor(IDFDatabaseManager(path))
            result = processor.execute(command)
        for line in result.lines:
            print(line)
        if result.exit_requested and session.request_close():
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


@coordinated_launcher("lanwire")
def main(argv: list[str] | None = None) -> int:
    initialize_language()
    configure_utf8_stdio()
    arguments = list(sys.argv[1:] if argv is None else argv)
    arguments = normalize_help_arguments(arguments)
    parser = build_parser()
    default_database = parser.get_default("database")
    parser.set_defaults(database=None)
    args = parser.parse_args(arguments)
    if getattr(args, "gui", False):
        from lanctl.apps.suite.launcher_gui import run_gui

        return run_gui("lanwire", database=args.database)
    with physical_console_session(
        args.database if args.database is not None else default_database,
        follow_project=args.database is None,
    ) as session:
        with session.operation() as path:
            if args.database is None:
                args.database = default_database
        if args.tui or args.cli or args.command in {None, "tui", "cli"}:
            return _run(args)
        with session.operation() as path:
            args.database = str(path)
            code = _run(args)
        return code if session.request_close(interactive=False) else 1


def _run(args):
    if args.tui or args.command == "tui" or (not args.cli and args.command is None):
        from lanctl.apps.wire.tui import run_tui

        return run_tui(args.database)
    if args.cli or args.command == "cli":
        return run_cli(args.database)

    processor = CommandProcessor(IDFDatabaseManager(args.database))
    result = processor.execute_parts(_command_parts(args))
    for line in result.lines:
        print(line)
    return 1 if result.lines and result.lines[0].startswith(t("LANCTL.UI.TEXT.ERROR")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
