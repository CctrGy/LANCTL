from __future__ import annotations

import argparse
import ipaddress
from datetime import datetime

from app.core.config import load_config
from app.core.console import ok
from app.core.database import DeviceDatabase
from app.core.group_database import GroupDatabase
from app.core.output import write_records
from app.services.lan_scanner import LanScanner, local_ipv4, resolve_network
from app.services.lan_scanner import DISCOVERY_MODES
from app.services.scan_profiles import SCAN_PROFILES, apply_profile
from app.core.progress import ScanProgress
from app.core.query import matches_query


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
        choices=("table", "json", "csv", "html", "xml"),
        default="table",
        help="Formato de salida (por defecto: table).",
    )
    command.add_argument("-o", "--output", help="Guarda la salida en un archivo.")
    command.add_argument(
        "--where",
        help='Consulta combinable, por ejemplo: "active and group=IOT and vendor~Amazon".',
    )
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
        default=None,
        help=(
            "Método: icmp, arp activo o hybrid (por defecto según settings)."
        ),
    )
    profiles = command.add_mutually_exclusive_group()
    profiles.add_argument(
        "--profile",
        choices=tuple(SCAN_PROFILES),
        default=None,
        help="Perfil completo de escaneo: fast, normal o accurate.",
    )
    profiles.add_argument("--fast", dest="profile", action="store_const", const="fast", help="Escaneo ARP rápido.")
    profiles.add_argument("--normal", dest="profile", action="store_const", const="normal", help="Escaneo híbrido equilibrado.")
    profiles.add_argument("--accurate", dest="profile", action="store_const", const="accurate", help="Escaneo profundo con varios métodos.")
    progress_options = command.add_mutually_exclusive_group()
    progress_options.add_argument("--progress", dest="progress", action="store_true", help="Muestra el progreso interactivo.")
    progress_options.add_argument("--no-progress", dest="progress", action="store_false", help="Oculta el progreso.")
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
    command.add_argument(
        "--show-detection",
        action="store_true",
        help="Añade los métodos históricos y la fecha de última detección.",
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
        progress=bool(config.get("progress", True)),
        configured_profile=config.get("scanProfile", "normal"),
        configured_discovery=config.get("discovery", "hybrid"),
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
        if not matches_query(device, active, getattr(args, "where", None)):
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

    profile_name = args.profile or args.configured_profile
    profile, effective_timeout, effective_workers = apply_profile(
        profile_name, args.timeout, args.workers
    )
    discovery = args.discovery or (
        profile.discovery if args.profile else args.configured_discovery
    )
    scanner = LanScanner(
        network=network,
        workers=effective_workers,
        timeout=effective_timeout,
        max_hosts=args.max_hosts,
    )
    progress = ScanProgress(args.progress)
    records = scanner.scan(
        include_unknown=args.include_unknown,
        resolve_names=args.resolve_names or profile.resolve_names,
        discovery=discovery,
        include_arp_cache=args.include_arp_cache,
        attempts=profile.attempts,
        extra_methods=profile.extra_methods,
        progress=progress,
    )
    seen_at = datetime.now().astimezone().isoformat(timespec="seconds")
    for record in records:
        methods = scanner.discovery_for(record).split("+")
        # CACHE es información histórica, no una confirmación de presencia.
        confirmed_methods = [
            method for method in methods if method not in ("-", "CACHE", "BASIC")
        ]
        if scanner.is_confirmed(record) and confirmed_methods:
            record.discovery_methods = confirmed_methods
            record.last_discovery = "+".join(confirmed_methods)
            record.last_seen = seen_at

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
    if args.show_detection:
        for column in ("detected-by", "last-seen"):
            if column not in columns:
                columns.append(column)
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
        f"Perfil: {profile.name} | Descubrimiento: {discovery} | ICMP: {icmp_count} | "
        f"ARP: {arp_count} | Cache no verificada: {cache_count}",
    )
    return 0
