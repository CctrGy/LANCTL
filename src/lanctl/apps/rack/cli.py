"""CLI y TUI de visualización de LANRACK."""

from __future__ import annotations

import json
import sys
from contextlib import suppress

from lanctl import __version__
from lanctl.apps.rack.service import RackService
from lanctl.apps.wire.idf.database import DEFAULT_DATABASE_PATH
from lanctl.core.config import load_config
from lanctl.core.parser import LANCTLArgumentParser, normalize_help_arguments
from lanctl.core.projects.console_session import physical_console_session
from lanctl.core.session import coordinated_launcher
from lanctl.shared.i18n import initialize_language, t


def configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            with suppress(AttributeError, OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")


def build_parser() -> LANCTLArgumentParser:
    parser = LANCTLArgumentParser(
        prog="LANRACK", description=t("LANCTL.UI.TEXT.DISPLAY_RACKS_AND_THEIR_EQUIPMENT")
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
        help=t("LANCTL.UI.TEXT.SHARED_PHYSICAL_IDF_DATABASE"),
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
        "--cli", "-cli", action="store_true", help=t("LANCTL.UI.TEXT.OPEN_THE_INTERACTIVE_CONSOLE")
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("list", aliases=["ls"], help=t("LANCTL.UI.TEXT.LIST_AVAILABLE_RACKS"))
    show = commands.add_parser("show", help=t("LANCTL.UI.TEXT.SHOW_A_RACK_AND_ITS_OCCUPANTS"))
    show.add_argument("rack", help=t("LANCTL.UI.TEXT.RACK_ID_OR_NAME"))
    dimensions = commands.add_parser(
        "dimensions", help=t("LANCTL.UI.TEXT.EDIT_THE_RACK_HEIGHT_AND_MOUNTING_WIDTH")
    )
    dimensions.add_argument("rack", help=t("LANCTL.UI.TEXT.RACK_ID"))
    dimensions.add_argument(
        "--units", type=int, required=True, help=t("LANCTL.UI.TEXT.HEIGHT_FROM_4_TO_52_U")
    )
    dimensions.add_argument(
        "--width-inches",
        type=int,
        choices=(10, 19, 21, 23),
        required=True,
        help=t("LANCTL.UI.TEXT.MOUNTING_WIDTH_IN_INCHES"),
    )
    commands.add_parser("elements", help=t("LANCTL.UI.TEXT.LIST_ALL_ELEMENTS_LOCATIONS_AND_TRAYS"))
    add = commands.add_parser(
        "add-element", help=t("LANCTL.UI.TEXT.CREATE_A_SHARED_PHYSICAL_ELEMENT")
    )
    add.add_argument(
        "--kind", required=True, help=t("LANCTL.UI.TEXT.EQUIPMENT_PANEL_OUTLET_OR_TRAY_PROFILE")
    )
    add.add_argument("--prefix", required=True, help=t("LANCTL.UI.TEXT.IDF_PREFIX"))
    add.add_argument("--name", default="", help=t("LANCTL.UI.TEXT.ELEMENT_NAME"))
    edit = commands.add_parser(
        "element", help=t("LANCTL.UI.TEXT.EDIT_OR_RELOCATE_AN_ELEMENT_WITHOUT_CHANGING_ITS_LINKS")
    )
    edit.add_argument("element", help=t("LANCTL.UI.TEXT.ELEMENT_ID"))
    edit.add_argument("--name", help=t("LANCTL.UI.TEXT.ELEMENT_NAME"))
    edit.add_argument("--description", help=t("LANCTL.UI.TEXT.ELEMENT_DESCRIPTION"))
    edit.add_argument(
        "--placement",
        choices=("inside", "environment", "independent", "hosted"),
        help=t("LANCTL.UI.TEXT.PHYSICAL_CLASSIFICATION"),
    )
    edit.add_argument("--rack", help=t("LANCTL.UI.TEXT.DESTINATION_RACK_ID"))
    edit.add_argument("--unit", type=int, help=t("LANCTL.UI.TEXT.STARTING_MOUNTING_UNIT"))
    edit.add_argument(
        "--height-u", type=int, help=t("LANCTL.UI.TEXT.HEIGHT_OCCUPIED_BY_THE_ELEMENT")
    )
    edit.add_argument("--tray", help=t("LANCTL.UI.TEXT.TRAY_HOUSING_THE_DEVICE"))
    return parser


def _print_rack(rack: dict) -> None:
    print(
        t(
            "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUEU_VALUE_INCHES_VALUE_ELEMENTS",
            value0=f"{rack['id']}",
            value1=f"{rack['name']}",
            value2=f"{rack['units']}",
            value3=f"{rack['widthInches'] or '?'}",
            value4=f"{len(rack['occupants'])}",
        )
    )
    for warning in rack["dimensions"]["warnings"]:
        print(t("LANCTL.UI.DETAIL.REVIEW_VALUE", value0=f"{warning}"))
    for item in rack["occupants"]:
        placement = item.get("placement", {})
        unit = (
            f"U{item['unit']}-{item['unit'] + item['span'] - 1}"
            if item["unit"]
            else placement.get("kind", "review")
        )
        print(f"  {unit:>4}  {item['id']:<10} {item['name'] or item['type']}")


def _element_command(service, args):
    if args.command == "elements":
        print(json.dumps(service.elements(), indent=2, ensure_ascii=False))
        return True
    if args.command == "add-element":
        service.edit_element(
            service.snapshot()["organizationRevision"],
            "create",
            "",
            {"kind": args.kind, "prefix": args.prefix, "name": args.name},
        )
        return True
    if args.command != "element":
        return False
    values = {k: getattr(args, k) for k in ("name", "description") if getattr(args, k) is not None}
    if args.height_u is not None:
        values["heightU"] = args.height_u
    if args.placement:
        if args.placement in {"inside", "environment"} and not args.rack:
            raise ValueError("Indica --rack para esta clasificación")
        if args.placement == "hosted" and not args.tray:
            raise ValueError("Indica --tray para alojar el dispositivo")
        values.update(
            rack=args.rack if args.placement in {"inside", "environment"} else None,
            in_rack=args.placement == "inside",
            unit=args.unit if args.placement == "inside" else 0,
            tray=args.tray if args.placement == "hosted" else None,
        )
    elif args.rack is not None or args.unit is not None or args.tray is not None:
        raise ValueError("Indica --placement al cambiar la ubicación")
    service.edit_element(service.snapshot()["organizationRevision"], "update", args.element, values)
    return True


def run_tui(service: RackService) -> int:
    return _console(service, tui=True)


@coordinated_launcher("lanrack")
def main(argv: list[str] | None = None) -> int:
    initialize_language()
    configure_utf8_stdio()
    arguments = normalize_help_arguments(list(sys.argv[1:] if argv is None else argv))
    parser = build_parser()
    default_database = parser.get_default("database")
    parser.set_defaults(database=None)
    args = parser.parse_args(arguments)
    if getattr(args, "gui", False):
        from lanctl.apps.suite.launcher_gui import run_gui

        return run_gui("lanrack", database=args.database)
    from lanctl.core.projects.physical_mutations import PhysicalSaveError

    try:
        with physical_console_session(
            args.database if args.database is not None else default_database,
            follow_project=args.database is None,
        ) as session:
            with session.operation() as path:
                if args.database is None:
                    args.database = default_database
            if args.tui or args.command is None:
                return _run(args)
            with session.operation() as path:
                args.database = str(path)
                code = _run(args)
            return code if session.request_close(interactive=False) else 1
    except PhysicalSaveError as error:
        print(t("LANCTL.UI.DETAIL.ERROR_VALUE", value0=f"{error}"))
        return 1


def _run(args):
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
    if args.command == "dimensions":
        service.set_dimensions(
            service.snapshot()["organizationRevision"],
            args.rack,
            {"units": args.units, "widthInches": args.width_inches},
        )
        _print_rack(service.get(args.rack))
        return 0
    if _element_command(service, args):
        return 0
    return run_cli(service)


def run_cli(service: RackService) -> int:
    return _console(service)


def _console(service: RackService, *, tui=False) -> int:
    with physical_console_session(service.database.path) as session:
        session.start()
        return _session_console(session, service, tui=tui)


def _session_console(session, service, *, tui=False):
    from lanctl.core.interactive_console import command_console

    with session.operation():
        pass

    def current_service(path):
        nonlocal service
        if service.database.path.resolve() != path:
            service = RackService(str(path))
        return service

    def dispatch(words):
        with session.operation() as path:
            return dispatch_to(current_service(path), words)

    def dispatch_to(service, words):
        args = build_parser().parse_args(words)
        if args.command in {"list", "ls"}:
            for rack in service.list():
                _print_rack(rack)
        elif args.command == "show":
            _print_rack(service.get(args.rack))
        elif args.command == "dimensions":
            service.set_dimensions(
                service.snapshot()["organizationRevision"],
                args.rack,
                {"units": args.units, "widthInches": args.width_inches},
            )
            _print_rack(service.get(args.rack))
        elif not _element_command(service, args):
            build_parser().print_help()
        return 0

    def overview():
        with session.operation() as path:
            rows = current_service(path).list()
        inventory = "\n".join(
            t(
                "LANCTL.UI.SUMMARY.VALUE_VALUE_VALUEU_VALUE_INCHES_VALUE_ELEMENTS_0F275CC5",
                value0=f"{row['id']:<12}",
                value1=f"{row['name']}",
                value2=f"{row['units']}",
                value3=f"{row['widthInches'] or '?'}",
                value4=f"{len(row['occupants'])}",
            )
            + (" · REVISAR DIMENSIONES" if row["dimensions"]["needsReview"] else "")
            for row in rows
        )
        return (
            (inventory or "No hay racks definidos en LANWIRE.")
            + "\n\nlist: listar · show ID: unidades y ocupantes · R: refrescar\ndimensions ID --units U --width-inches ANCHO: editar dimensiones.\nelements · add-element --kind tray --prefix TR · element ID --placement inside --rack RK-ID --unit U --height-u N"
        )

    return command_console(
        "LANRACK",
        dispatch,
        tui=tui,
        overview=overview,
        shortcuts={"r": ["list"]},
        on_close=session.request_close,
        notifications=session.messages,
    )
