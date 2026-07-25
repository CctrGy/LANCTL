from __future__ import annotations

import argparse

from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase
from app.core.group_database import GroupDatabase
from app.core.output import write_records


FIELDS = ("cnf", "name", "description", "alias", "group", "protocol")


def register_element_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "element",
        help="Edita un elemento identificado por IP, MAC o alias.",
    )
    command.add_argument("selector", nargs="?", help="IP, MAC o alias.")
    command.add_argument(
        "action",
        nargs="?",
        choices=("edit", *FIELDS),
        help="Campo o acción que se quiere editar.",
    )
    command.add_argument("values", nargs="*", help="Nuevo valor.")
    command.add_argument(
        "-add",
        metavar="MAC",
        help="Añade un elemento nuevo utilizando su dirección MAC.",
    )
    command.add_argument("-name", dest="new_name", help="Nombre inicial opcional.")
    command.add_argument("-alias", dest="new_alias", help="Alias inicial opcional.")
    command.add_argument(
        "-description",
        dest="new_description",
        help="Descripción inicial opcional (máximo 32 caracteres).",
    )
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.add_argument("--groups", default=config["groups"], help="Archivo JSON de grupos.")
    command.set_defaults(handler=run_element)


def run_element(args: argparse.Namespace) -> int:
    database = DeviceDatabase(args.database)
    if args.add:
        if args.selector or args.action or args.values:
            raise ValueError(
                "usa: element -add MAC [-name NAME] [-alias ALIAS] "
                "[-description DESCRIPTION]"
            )
        device = database.add_device(
            args.add,
            name=args.new_name or "",
            alias=args.new_alias or "",
            description=args.new_description or "-",
        )
        ok(
            "ANADIDO",
            f"{device.mac} | {device.alias or device.name or 'sin etiqueta'}",
        )
        return 0

    if not args.selector:
        raise ValueError("indica un elemento o usa element -add MAC")
    if args.action is None:
        device = database.resolve(args.selector)
        write_records(
            [device],
            output_format="table",
            include_manufacturer=True,
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
        ok("ACTUALIZADO", f"{device.alias or device.ip} -> {group.name}")
    elif field == "protocol":
        parts = value.split()
        protocol = parts[-1]
        enabled = not (len(parts) > 1 and parts[0].casefold() in ("del", "delete", "remove"))
        device = database.set_protocol(args.selector, protocol, enabled)
        ok(
            "ACTUALIZADO",
            f"{device.alias or device.ip} | protocols = {', '.join(device.protocols) or '-'}",
        )
    else:
        device = database.edit_device(args.selector, field, value)
        shown = getattr(device, field)
        ok("ACTUALIZADO", f"{device.alias or device.ip} | {field} = {shown}")
    return 0
