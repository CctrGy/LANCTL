from __future__ import annotations

import argparse
import os
import sys

from colorama import Fore, Style

from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase
from app.core.group_database import GroupDatabase
from app.core.layout import fit_text, shrink_widths, terminal_columns


def register_group_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "group",
        help="Crea, edita y consulta grupos de elementos.",
    )
    command.add_argument("name", nargs="?", help="Nombre del grupo.")
    actions = command.add_mutually_exclusive_group()
    actions.add_argument("-new", action="store_true", help="Crea el grupo.")
    actions.add_argument("-del", dest="delete", action="store_true", help="Elimina el grupo.")
    actions.add_argument("-rename", metavar="NUEVO", help="Renombra el grupo.")
    actions.add_argument("-description", metavar="TEXTO", help="Edita su descripción.")
    actions.add_argument("-add", metavar="ELEMENTO", help="Añade IP, MAC o alias.")
    actions.add_argument("-remove", metavar="ELEMENTO", help="Retira IP, MAC o alias.")
    actions.add_argument(
        "-list",
        action="store_true",
        help="Lista los elementos que pertenecen al grupo.",
    )
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.add_argument("--groups", default=config["groups"], help="Archivo JSON de grupos.")
    command.set_defaults(handler=run_group)


def run_group(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    groups = GroupDatabase(args.groups, database)

    if args.new:
        if not args.name:
            raise ValueError("indica el nombre: group -new NOMBRE")
        group = groups.create(args.name)
        ok("CREADO", f"Grupo {group.name}")
    elif args.delete:
        if not args.name:
            raise ValueError("indica el nombre: group -del NOMBRE")
        groups.delete(args.name)
        ok("ELIMINADO", f"Grupo {args.name.upper()}")
    elif args.rename is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -rename NUEVO")
        group = groups.rename(args.name, args.rename)
        ok("ACTUALIZADO", f"Grupo renombrado a {group.name}")
    elif args.description is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -description TEXTO")
        group = groups.set_description(args.name, args.description)
        ok("ACTUALIZADO", f'{group.name} | "{group.description}"')
    elif args.add is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -add ELEMENTO")
        group, device = groups.add(args.name, args.add)
        ok("ANADIDO", f"{device.alias or device.ip} -> {group.name}")
    elif args.remove is not None:
        if not args.name:
            raise ValueError("usa: group NOMBRE -remove ELEMENTO")
        group, device = groups.remove(args.name, args.remove)
        ok("RETIRADO", f"{device.alias or device.ip} <- {group.name}")
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
                widths, {"group": 8, "count": 8, "description": 8}, fields,
                terminal_columns(), ("description", "group"), gap=2,
            )
            if stacked:
                for index, group in enumerate(stored):
                    if index:
                        print(_paint("-" * (terminal_columns() or 40), Style.DIM, use_color))
                    print(f"{_paint('GROUP', Fore.CYAN, use_color, bright=True)}: {_paint(group.name, Fore.YELLOW, use_color)}")
                    print(f"{_paint('ELEMENTS', Fore.CYAN, use_color, bright=True)}: {_paint(str(len(group.members)), Fore.GREEN, use_color)}")
                    print(f"{_paint('DESCRIPTION', Fore.CYAN, use_color, bright=True)}: {_paint(group.description, Fore.WHITE, use_color)}")
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
    rows = [((devices.get(mac).alias or devices.get(mac).name or "-") if devices.get(mac) else "-",
             devices.get(mac).ip if devices.get(mac) else "-", mac) for mac in group.members]
    fields = ("element", "ip", "mac")
    widths = {"element": max(16, *(len(row[0]) for row in rows)), "ip": 15, "mac": 17}
    widths, stacked = shrink_widths(widths, {"element": 5, "ip": 7, "mac": 17}, fields,
                                    terminal_columns(), ("element", "ip"), gap=2)
    if stacked:
        for index, (label, ip, mac) in enumerate(rows):
            if index:
                print(_paint("-" * (terminal_columns() or 40), Style.DIM, use_color))
            print(f"ELEMENT: {_paint(label, Fore.YELLOW, use_color)}")
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
