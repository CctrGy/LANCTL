from __future__ import annotations

import argparse

from lanctl.core.config import load_config
from lanctl.core.console import ok
from lanctl.core.database import DeviceDatabase
from lanctl.core.group_database import GroupDatabase
from lanctl.core.output import write_records

FIELDS = ("ip", "cnf", "name", "description", "alias", "idf", "group", "protocol")
DELETE_ACTIONS = ("delete", "del", "remove")


def register_element_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "element",
        help="Edita uno o varios campos de un elemento identificado por IP, MAC o alias.",
    )
    command.add_argument("selector", nargs="?", help="IP, MAC o alias.")
    command.add_argument(
        "action",
        nargs="?",
        choices=("edit", *FIELDS, *DELETE_ACTIONS),
        help="Campo o acción que se quiere editar.",
    )
    command.add_argument("values", nargs="*", help="Nuevo valor.")
    command.add_argument(
        "-add",
        metavar="MAC",
        help="Añade un elemento nuevo utilizando su dirección MAC.",
    )
    command.add_argument(
        "-name", "--name", dest="new_name", help="Asigna NAME al elemento indicado."
    )
    command.add_argument("-ip", "--ip", dest="new_ip", help="Asigna una dirección IPv4.")
    command.add_argument(
        "-alias", "--alias", dest="new_alias", help="Asigna ALIAS al elemento indicado."
    )
    command.add_argument(
        "-description",
        "--description",
        dest="new_description",
        help="Asigna DESCRIPTION al elemento indicado (máximo 42 caracteres).",
    )
    command.add_argument("-cnf", "--cnf", dest="new_cnf", help="Asigna el estado CNF.")
    command.add_argument(
        "-idf", "--idf", dest="new_idf", help="Asigna un IDF único (2-5 letras y 2-5 dígitos)."
    )
    command.add_argument("-group", "--group", dest="new_group", help="Añade el elemento al grupo.")
    command.add_argument(
        "-protocol", "--protocol", dest="new_protocol", help="Activa un protocolo."
    )
    command.add_argument(
        "-delete",
        "--delete",
        dest="delete_requested",
        action="store_true",
        help="Elimina completamente el elemento indicado.",
    )
    command.add_argument(
        "--database", default=config["database"], help="Archivo JSON de elementos."
    )
    command.add_argument("--groups", default=config["groups"], help="Archivo JSON de grupos.")
    command.add_argument(
        "--yes",
        action="store_true",
        help="Elimina sin solicitar confirmación.",
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
            "ANADIDO",
            f"{device.mac} | {device.alias or device.name or 'sin etiqueta'}",
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
            "ACTUALIZADO",
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
            answer = input(f"Eliminar completamente {label} ({device.mac})? [s/N]: ")
            if answer.strip().casefold() not in ("s", "si", "sí", "y", "yes"):
                ok("CANCELADO", "No se ha eliminado ningún elemento.")
                return 1
        deleted = GroupDatabase(args.groups, database).delete_device(args.selector)
        ok(
            "ELIMINADO",
            f"{deleted.mac} | retirado de la base y de todos los grupos",
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
