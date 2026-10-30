from __future__ import annotations

import argparse
import os
import sys

from colorama import Fore, Style

from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.database import DeviceDatabase
from lanctl.core.group_database import GroupDatabase
from lanctl.core.layout import fit_text, shrink_widths, terminal_columns
from lanctl.shared.i18n import t


def register_group_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "group",
        help=t("LANCTL.UI.HELP.CREATE_EDIT_AND_QUERY_ELEMENT_GROUPS"),
    )
    command.add_argument("name", nargs="?", help=t("LANCTL.UI.HELP.GROUP_NAME"))
    actions = command.add_mutually_exclusive_group()
    actions.add_argument("-new", action="store_true", help=t("LANCTL.UI.HELP.CREATE_THE_GROUP"))
    actions.add_argument(
        "-del", dest="delete", action="store_true", help=t("LANCTL.UI.HELP.DELETE_THE_GROUP")
    )
    actions.add_argument("-rename", metavar="NUEVO", help=t("LANCTL.UI.HELP.RENAME_THE_GROUP"))
    actions.add_argument(
        "-description", metavar="TEXTO", help=t("LANCTL.UI.HELP.EDIT_ITS_DESCRIPTION")
    )
    actions.add_argument(
        "-add", metavar=t("LANCTL.UI.STATUS.ELEMENT"), help=t("LANCTL.UI.HELP.ADD_IP_MAC_OR_ALIAS")
    )
    actions.add_argument(
        "-remove",
        metavar=t("LANCTL.UI.STATUS.ELEMENT"),
        help=t("LANCTL.UI.HELP.REMOVE_IP_MAC_OR_ALIAS"),
    )
    actions.add_argument(
        "-list",
        action="store_true",
        help=t("LANCTL.UI.HELP.LIST_ELEMENTS_BELONGING_TO_THE_GROUP"),
    )
    command.add_argument(
        "--database", default=config["database"], help=t("LANCTL.UI.HELP.ELEMENT_JSON_FILE")
    )
    command.add_argument(
        "--groups", default=config["groups"], help=t("LANCTL.UI.HELP.GROUP_JSON_FILE")
    )
    command.set_defaults(handler=run_group)


def run_group(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    groups = GroupDatabase(args.groups, database)

    if args.new:
        if not args.name:
            raise ValueError("indica el nombre: group -new NOMBRE")
        group = groups.create(args.name)
        ok(t("LANCTL.UI.STATUS.CREATED"), t("LANCTL.UI.DETAIL.GROUP_VALUE", value0=f"{group.name}"))
    elif args.delete:
        if not args.name:
            raise ValueError("indica el nombre: group -del NOMBRE")
        groups.delete(args.name)
        ok(
            t("LANCTL.UI.STATUS.DELETED_D7B7F127"),
            t("LANCTL.UI.DETAIL.GROUP_VALUE", value0=f"{args.name.upper()}"),
        )
    elif args.rename is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -rename NUEVO")
        group = groups.rename(args.name, args.rename)
        ok(
            t("LANCTL.UI.STATUS.UPDATED"),
            t("LANCTL.UI.MESSAGE.GROUP_RENAMED_TO_VALUE", value0=f"{group.name}"),
        )
    elif args.description is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -description TEXTO")
        group = groups.set_description(args.name, args.description)
        ok(t("LANCTL.UI.STATUS.UPDATED"), f'{group.name} | "{group.description}"')
    elif args.add is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -add ELEMENTO")
        group, device = groups.add(args.name, args.add)
        ok(t("LANCTL.UI.STATUS.ADDED"), f"{device.alias or device.ip} -> {group.name}")
    elif args.remove is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -remove ELEMENTO")
        group, device = groups.remove(args.name, args.remove)
        ok(t("LANCTL.UI.STATUS.REMOVED"), f"{device.alias or device.ip} <- {group.name}")
    elif args.list:
        if not args.name:
            raise ValueError("usa: group NOMBRE -list")
        stored = groups.load()
        group = groups._find(stored, args.name)
        _print_group(group, database)
    else:
        stored = groups.load()
        if args.name:
            group = groups._find(stored, args.name)
            _print_group(group, database)
        else:
            use_color = _use_color()
            fields = ("group", "count", "description")
            widths = {
                "group": max(16, *(len(group.name) for group in stored)),
                "count": 8,
                "description": max(42, *(len(group.description) for group in stored)),
            }
            widths, stacked = shrink_widths(
                widths,
                {"group": 8, "count": 8, "description": 8},
                fields,
                terminal_columns(),
                ("description", "group"),
                gap=2,
            )
            if stacked:
                for index, group in enumerate(stored):
                    if index:
                        print(
                            _paint(
                                "-" * (terminal_columns() or 40),
                                Style.DIM,
                                use_color,
                            )
                        )
                    print(
                        f"{_paint('GROUP', Fore.CYAN, use_color, bright=True)}: {_paint(group.name, Fore.YELLOW, use_color)}"
                    )
                    print(
                        f"{_paint('ELEMENTS', Fore.CYAN, use_color, bright=True)}: {_paint(str(len(group.members)), Fore.GREEN, use_color)}"
                    )
                    print(
                        f"{_paint('DESCRIPTION', Fore.CYAN, use_color, bright=True)}: {_paint(group.description, Fore.WHITE, use_color)}"
                    )
                return 0
            print(
                f"{_paint('GROUP'.ljust(widths['group']), Fore.CYAN, use_color, bright=True)}  "
                f"{_paint('ELEMENTS'.rjust(widths['count']), Fore.CYAN, use_color, bright=True)}  "
                f"{_paint('DESCRIPTION', Fore.CYAN, use_color, bright=True)}"
            )
            separator = "  ".join("-" * widths[field] for field in fields)
            print(_paint(separator, Style.DIM, use_color))
            for group in stored:
                print(
                    f"{_paint(fit_text(group.name, widths['group']).ljust(widths['group']), Fore.YELLOW, use_color)}  "
                    f"{_paint(str(len(group.members)).rjust(widths['count']), Fore.GREEN, use_color)}  "
                    f"{_paint(fit_text(group.description, widths['description']), Fore.WHITE, use_color)}"
                )
    return 0


def _print_group(group, database: DeviceDatabase) -> None:
    use_color = _use_color()
    print(
        f"{_paint(group.name, Fore.YELLOW, use_color, bright=True)}  "
        f"{_paint(group.description, Fore.WHITE, use_color)}"
    )
    devices = {device.mac: device for device in database.load()}
    rows = [
        (
            (devices.get(mac).alias or devices.get(mac).name or "-") if devices.get(mac) else "-",
            devices.get(mac).ip if devices.get(mac) else "-",
            mac,
        )
        for mac in group.members
    ]
    fields = ("element", "ip", "mac")
    widths = {"element": max(16, *(len(row[0]) for row in rows)), "ip": 15, "mac": 17}
    widths, stacked = shrink_widths(
        widths,
        {"element": 5, "ip": 7, "mac": 17},
        fields,
        terminal_columns(),
        ("element", "ip"),
        gap=2,
    )
    if stacked:
        for index, (label, ip, mac) in enumerate(rows):
            if index:
                print(
                    _paint(
                        "-" * (terminal_columns() or 40),
                        Style.DIM,
                        use_color,
                    )
                )
            print(t("LANCTL.CLI.ELEMENT.LABEL", value=_paint(label, Fore.YELLOW, use_color)))
            print(f"IP     : {_paint(ip, Fore.CYAN, use_color)}")
            print(f"MAC    : {_paint(mac, Fore.MAGENTA, use_color)}")
        return
    print(
        f"{_paint('ELEMENT'.ljust(widths['element']), Fore.CYAN, use_color, bright=True)}  "
        f"{_paint('IP'.ljust(widths['ip']), Fore.CYAN, use_color, bright=True)}  "
        f"{_paint('MAC', Fore.CYAN, use_color, bright=True)}"
    )
    separator = "  ".join("-" * widths[field] for field in fields)
    print(_paint(separator, Style.DIM, use_color))
    for label, ip, mac in rows:
        print(
            f"{_paint(fit_text(label, widths['element']).ljust(widths['element']), Fore.YELLOW, use_color)}  "
            f"{_paint(fit_text(ip, widths['ip']).ljust(widths['ip']), Fore.CYAN, use_color)}  "
            f"{_paint(mac, Fore.MAGENTA, use_color)}"
        )


def _use_color() -> bool:
    return sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _paint(text: str, color: str, enabled: bool, bright: bool = False) -> str:
    if not enabled:
        return text
    intensity = Style.BRIGHT if bright else ""
    return f"{intensity}{color}{text}{Style.RESET_ALL}"
