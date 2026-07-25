from __future__ import annotations

import argparse
import ipaddress

from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase
from app.core.group_database import GroupDatabase
from app.core.output import write_records
from app.services.lan_scanner import LanScanner, local_ipv4, resolve_network
from app.services.lan_scanner import DISCOVERY_MODES


def register_list_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "list",
        help="Escanea la LAN y muestra dispositivos activos e históricos.",
        description=(
            "Realiza un escaneo básico de IP/MAC, actualiza la base de datos "
            "por MAC y muestra también los equipos no detectados."
        ),
    )
    command.add_argument(
        "--network",
        default=config["range"],
        help="Red CIDR. Por defecto detecta la LAN como /24.",
    )
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.add_argument("--groups", default=config["groups"], help="Archivo JSON de grupos.")
    command.add_argument(
        "-f",
        "--format",
        choices=("table", "json", "csv"),
        default="table",
        help="Formato de salida (por defecto: table).",
    )
    command.add_argument("-o", "--output", help="Guarda la salida en un archivo.")
    command.add_argument(
        "-w",
        "--workers",
        type=int,
        default=config["workers"],
        help="Comprobaciones simultáneas.",
    )
    command.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=config["timeout"],
        help="Segundos por host.",
    )
    command.add_argument(
        "--include-unknown",
        action="store_true",
        help="Incluye hosts activos aunque todavía no tengan MAC.",
    )
    command.add_argument(
        "--resolve-names",
        action="store_true",
        help="Resuelve y guarda nombres DNS de los elementos detectados.",
    )
    command.add_argument(
        "--max-hosts",
        type=int,
        default=config["maxHosts"],
        help="Máximo de hosts permitido en un escaneo.",
    )
    command.add_argument(
        "--discovery",
        choices=DISCOVERY_MODES,
        default=config["discovery"],
        help=(
            "Método: icmp, arp activo o hybrid (por defecto según settings)."
        ),
    )
    command.add_argument(
        "--show-discovery",
        action="store_true",
        help="Añade una columna con ICMP, ARP, LOCAL, BASIC o CACHE.",
    )
    command.add_argument(
        "--include-arp-cache",
        action="store_true",
        help=(
            "Importa vecinos ARP en caché como CACHE no verificada; "
            "no cuentan como activos."
        ),
    )
    connection = command.add_mutually_exclusive_group()
    connection.add_argument(
        "--active",
        "-active",
        "-connected",
        "--connected",
        "-conected",
        dest="connected",
        action="store_true",
        help="Muestra solo los dispositivos activos en el escaneo actual.",
    )
    connection.add_argument(
        "-disconnected",
        "--disconnected",
        "-offline",
        action="store_true",
        help="Muestra solo los dispositivos no detectados actualmente.",
    )
    command.add_argument(
        "-basic",
        "--basic",
        action="store_true",
        help="Vista reducida: IP, alias y descripción.",
    )
    command.add_argument(
        "-cnf",
        "--cnf-state",
        choices=("O", "X", "-", "S"),
        type=str.upper,
        help="Filtra por estado CNF: O, X, - o S.",
    )
    command.add_argument(
        "-group",
        "--group",
        metavar="GRUPO",
        help="Muestra solo los elementos de un grupo.",
    )
    command.add_argument(
        "-dhcp",
        "--dhcp-only",
        action="store_true",
        help="Muestra solo IP incluidas en el rango DHCP configurado.",
    )
    command.set_defaults(
        handler=run_list,
        display_columns=config["listColumns"],
        dhcp_range=config["dhcpRange"],
    )


def active_flags(devices, records, scanner=None) -> list[bool]:
    if scanner is not None:
        return [scanner.is_confirmed(device) for device in devices]
    active_macs = {record.mac for record in records if record.mac}
    active_ips_without_mac = {record.ip for record in records if not record.mac}
    return [
        device.mac in active_macs
        if device.mac
        else device.ip in active_ips_without_mac
        for device in devices
    ]


def ip_in_range(value: str, configured_range: str | None) -> bool:
    if not configured_range:
        return False
    try:
        raw_start, raw_end = configured_range.split("-", 1)
        address = ipaddress.IPv4Address(value)
        start = ipaddress.IPv4Address(raw_start.strip())
        end = ipaddress.IPv4Address(raw_end.strip())
    except ValueError:
        return False
    return start <= address <= end


def filter_rows(devices, activity, args):
    selected = []
    for device, active in zip(devices, activity):
        if args.connected and not active:
            continue
        if args.disconnected and active:
            continue
        if args.cnf_state and device.cnf != args.cnf_state:
            continue
        if args.group and args.group.upper() not in device.groups:
            continue
        if args.dhcp_only and not ip_in_range(device.ip, args.dhcp_range):
            continue
        selected.append((device, active))
    return selected


def run_list(args: argparse.Namespace) -> int:
    if args.workers < 1:
        raise ValueError("--workers debe ser mayor que cero")
    if args.timeout <= 0:
        raise ValueError("--timeout debe ser mayor que cero")
    if args.max_hosts < 1:
        raise ValueError("--max-hosts debe ser mayor que cero")

    network = resolve_network(args.network)
    if args.network:
        local_ip = local_ipv4()
        if local_ip not in network:
            suggested = resolve_network(None)
            raise ValueError(
                f"la IP local {local_ip} no pertenece a {network}. "
                f"Usa --network {suggested} o no indiques --network."
            )

    scanner = LanScanner(
        network=network,
        workers=args.workers,
        timeout=args.timeout,
        max_hosts=args.max_hosts,
    )
    records = scanner.scan(
        include_unknown=args.include_unknown,
        resolve_names=args.resolve_names,
        discovery=args.discovery,
        include_arp_cache=args.include_arp_cache,
    )

    database = DeviceDatabase(args.database)
    devices = database.upsert(records)
    GroupDatabase(args.groups, database).ensure_basic(devices)
    # ensure_basic puede reescribir la base; se vuelve a cargar su resultado.
    devices = database.load()
    activity = active_flags(devices, records, scanner)
    selected = filter_rows(devices, activity, args)
    visible_devices = [device for device, _ in selected]
    visible_activity = [active for _, active in selected]
    columns = list(
        ("ip", "alias", "description") if args.basic else args.display_columns
    )
    if args.show_discovery and "discovery" not in columns:
        columns.append("discovery")
    display_rows = []
    for device in visible_devices:
        row = device.to_dict()
        row["discovery"] = scanner.discovery_for(device)
        display_rows.append(row)

    write_records(
        display_rows,
        output_format=args.format,
        destination=args.output,
        columns=columns,
        active_rows=visible_activity,
        section_ip_range=args.dhcp_range,
    )
    active_count = sum(visible_activity)
    icmp_count = sum(
        "ICMP" in scanner.discovery_for(record).split("+") for record in records
    )
    arp_count = sum(
        "ARP" in scanner.discovery_for(record).split("+") for record in records
    )
    cache_count = sum(
        "CACHE" in scanner.discovery_for(record).split("+") for record in records
    )
    ok(
        "LISTADO",
        f"Mostrados: {len(visible_devices)} | Activos: {active_count} | "
        f"No detectados: {len(visible_devices) - active_count} | "
        f"Total registrados: {len(devices)}\n"
        f"Descubrimiento: {args.discovery} | ICMP: {icmp_count} | "
        f"ARP: {arp_count} | Cache no verificada: {cache_count}",
    )
    return 0
