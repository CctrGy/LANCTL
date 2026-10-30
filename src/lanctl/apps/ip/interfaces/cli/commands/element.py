from __future__ import annotations

import argparse

from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.database import DeviceDatabase
from lanctl.core.group_database import GroupDatabase
from lanctl.core.output import write_records
from lanctl.shared.i18n import t

FIELDS = ("ip", "cnf", "name", "description", "alias", "idf", "group", "protocol")
DELETE_ACTIONS = ("delete", "del", "remove")


def register_element_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "element",
        help=t(
            "LANCTL.UI.HELP.EDIT_ONE_OR_MORE_FIELDS_OF_AN_ELEMENT_IDENTIFIED_BY_IP_MAC_OR_ALIAS"
        ),
    )
    command.add_argument("selector", nargs="?", help=t("LANCTL.UI.HELP.IP_MAC_OR_ALIAS"))
    command.add_argument(
        "action",
        nargs="?",
        choices=("edit", *FIELDS, *DELETE_ACTIONS),
        help=t("LANCTL.UI.HELP.FIELD_OR_ACTION_TO_EDIT"),
    )
    command.add_argument("values", nargs="*", help=t("LANCTL.UI.HELP.NEW_VALUE"))
    command.add_argument(
        "-add",
        metavar="MAC",
        help=t("LANCTL.UI.HELP.ADD_A_NEW_ELEMENT_USING_ITS_MAC_ADDRESS"),
    )
    command.add_argument(
        "-name",
        "--name",
        dest="new_name",
        help=t("LANCTL.UI.HELP.ASSIGN_NAME_TO_THE_SPECIFIED_ELEMENT"),
    )
    command.add_argument(
        "-ip", "--ip", dest="new_ip", help=t("LANCTL.UI.HELP.ASSIGN_AN_IPV4_ADDRESS")
    )
    command.add_argument(
        "-alias",
        "--alias",
        dest="new_alias",
        help=t("LANCTL.UI.HELP.ASSIGN_ALIAS_TO_THE_SPECIFIED_ELEMENT"),
    )
    command.add_argument(
        "-description",
        "--description",
        dest="new_description",
        help=t("LANCTL.UI.HELP.ASSIGN_DESCRIPTION_TO_THE_SPECIFIED_ELEMENT"),
    )
    command.add_argument(
        "-cnf", "--cnf", dest="new_cnf", help=t("LANCTL.UI.HELP.ASSIGN_THE_CNF_STATE")
    )
    command.add_argument(
        "-idf",
        "--idf",
        dest="new_idf",
        help=t("LANCTL.UI.HELP.ASSIGN_A_UNIQUE_IDF_2_5_LETTERS_AND_2_5_DIGITS"),
    )
    command.add_argument(
        "-group", "--group", dest="new_group", help=t("LANCTL.UI.HELP.ADD_THE_ELEMENT_TO_THE_GROUP")
    )
    command.add_argument(
        "-protocol", "--protocol", dest="new_protocol", help=t("LANCTL.UI.HELP.ENABLE_A_PROTOCOL")
    )
    command.add_argument(
        "-delete",
        "--delete",
        dest="delete_requested",
        action="store_true",
        help=t("LANCTL.UI.HELP.COMPLETELY_DELETE_THE_SPECIFIED_ELEMENT"),
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.add_argument(
        "--groups", default=config["groups"], help=t("LANCTL.UI.HELP.GROUP_JSON_FILE")
    )
    command.add_argument(
        "--yes",
        action="store_true",
        help=t("LANCTL.UI.HELP.DELETE_WITHOUT_REQUESTING_CONFIRMATION"),
    )
    command.set_defaults(handler=run_element)


def run_element(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    if args.add:
        if (
            args.selector
            or args.action
            or args.values
            or args.new_cnf
            or args.new_group
            or args.new_protocol
            or args.new_idf
            or args.delete_requested
        ):
            raise ValueError(
                "usa: element -add MAC [-ip IP] [-name NAME] [-alias ALIAS] "
                "[-description DESCRIPTION]"
            )
        device = database.add_device(
            args.add,
            ip=args.new_ip or "-",
            name=args.new_name or "",
            alias=args.new_alias or "",
            description=args.new_description or "-",
            idf=args.new_idf or "",
        )
        ok(
            t("LANCTL.UI.STATUS.ADDED"),
            f"{device.mac} | {device.alias or device.name or t('LANCTL.UI.VALUE.UNLABELED')}",
        )
        return 0

    if not args.selector:
        raise ValueError("indica un elemento o usa element -add MAC")

    option_edits = [
        ("ip", args.new_ip),
        ("name", args.new_name),
        ("alias", args.new_alias),
        ("description", args.new_description),
        ("cnf", args.new_cnf),
        ("idf", args.new_idf),
        ("group", args.new_group),
        ("protocol", args.new_protocol),
    ]
    requested_edits = [(field, value) for field, value in option_edits if value is not None]
    if args.delete_requested:
        if args.action or args.values or requested_edits:
            raise ValueError("-delete no se puede combinar con otra edición")
        args.action = "delete"
    elif requested_edits and (args.action or args.values):
        raise ValueError(
            "no mezcles la sintaxis posicional con opciones; usa varias opciones "
            "-ip/-name/-alias/-description/-cnf/-group/-protocol"
        )

    if requested_edits:
        stable_selector = database.resolve(args.selector).mac or args.selector
        groups = GroupDatabase(args.groups, database)
        updated = groups.edit_device_fields(stable_selector, requested_edits)
        changes: list[str] = []
        for field, value in requested_edits:
            if field == "group":
                changes.append(f"group += {value.upper()}")
            elif field == "protocol":
                parts = value.split()
                changes.append(f"protocols = {', '.join(updated.protocols) or '-'}")
            else:
                changes.append(f"{field} = {getattr(updated, field)}")
        ok(
            t("LANCTL.UI.STATUS.UPDATED"),
            f"{updated.alias or updated.ip} | " + " | ".join(changes),
        )
        return 0

    if args.action is None:
        device = database.resolve(args.selector)
        write_records(
            [device],
            output_format="table",
            columns=(
                "ip",
                "cnf",
                "alias",
                "mac",
                "name",
                "group",
                "description",
                "manufacturer",
                "detected-by",
                "last-discovery",
                "last-seen",
            ),
        )
        return 0

    if args.action in DELETE_ACTIONS:
        if args.values:
            raise ValueError("delete no acepta valores adicionales")
        device = database.resolve(args.selector)
        label = device.alias or device.name or device.ip
        if not args.yes:
            answer = input(
                t(
                    "LANCTL.UI.MESSAGE.COMPLETELY_DELETE_VALUE_VALUE_S_N",
                    value0=f"{label}",
                    value1=f"{device.mac}",
                )
            )
            if answer.strip().casefold() not in ("s", "si", "sí", "y", "yes"):
                ok(t("LANCTL.UI.STATUS.CANCELLED"), t("LANCTL.UI.PROMPT.NO_ELEMENTS_WERE_DELETED"))
                return 1
        deleted = GroupDatabase(args.groups, database).delete_device(args.selector)
        ok(
            t("LANCTL.UI.STATUS.DELETED_D7B7F127"),
            t(
                "LANCTL.UI.SUMMARY.VALUE_REMOVED_FROM_THE_DATABASE_AND_ALL_GROUPS",
                value0=f"{deleted.mac}",
            ),
        )
        return 0

    if not args.values:
        raise ValueError(f"falta el valor para element {args.selector} {args.action}")
    if args.action == "edit":
        if len(args.values) < 2:
            raise ValueError("usa: element ELEMENTO edit CAMPO VALOR")
        field = args.values[0].casefold()
        value = " ".join(args.values[1:])
    else:
        field = args.action
        value = " ".join(args.values)

    if field not in FIELDS:
        raise ValueError(f"campo no editable: {field}")
    if field == "group":
        group, device = GroupDatabase(args.groups, database).add(value, args.selector)
        ok(t("LANCTL.UI.STATUS.UPDATED"), f"{device.alias or device.ip} -> {group.name}")
    elif field == "protocol":
        parts = value.split()
        protocol = parts[-1]
        enabled = not (len(parts) > 1 and parts[0].casefold() in ("del", "delete", "remove"))
        device = database.set_protocol(args.selector, protocol, enabled)
        ok(
            t("LANCTL.UI.STATUS.UPDATED"),
            f"{device.alias or device.ip} | protocols = {', '.join(device.protocols) or '-'}",
        )
    else:
        device = database.edit_device(args.selector, field, value)
        shown = getattr(device, field)
        ok(t("LANCTL.UI.STATUS.UPDATED"), f"{device.alias or device.ip} | {field} = {shown}")
    return 0
