from __future__ import annotations

import argparse
import ipaddress
import json

from app.core.config import (
    CONFIG_PATH,
    load_config,
    normalize_dhcp_range,
    save_config,
)
from app.core.console import ok
from app.core.output import normalize_columns
from app.services.scan_profiles import SCAN_PROFILES


def register_settings_command(commands: argparse._SubParsersAction) -> None:
    command = commands.add_parser(
        "settings",
        help="Consulta o modifica la configuración persistente de LANCTL.",
    )
    command.add_argument(
        "-range",
        dest="network_range",
        metavar="CIDR",
        help="Rango LAN predeterminado, por ejemplo 192.168.1.1/24.",
    )
    command.add_argument(
        "-list-fields",
        "--list-fields",
        "-list",
        nargs="+",
        metavar="CAMPO",
        help="Columnas mostradas por list, separadas por espacios o comas.",
    )
    command.add_argument(
        "-dhcp-range",
        "--dhcp-range",
        "-dhcp",
        metavar="INICIO-FIN",
        help=(
            "Rango DHCP manual. Usa 'off' para dejarlo sin configurar."
        ),
    )
    command.add_argument(
        "-credentials",
        "--credentials",
        metavar="ARCHIVO",
        help="Ruta del almacén de credenciales cifradas.",
    )
    command.add_argument(
        "-discovery",
        "--discovery",
        choices=("icmp", "arp", "hybrid"),
        help="Método predeterminado utilizado por list.",
    )
    command.add_argument(
        "--scan-profile",
        choices=tuple(SCAN_PROFILES),
        help="Perfil predeterminado de list: fast, normal o accurate.",
    )
    command.add_argument("--progress", choices=("on", "off"), help="Activa o desactiva el progreso interactivo.")
    command.add_argument(
        "--service-identification",
        choices=("on", "off"),
        help="Activa o desactiva el reconocimiento de servicios en scan.",
    )
    command.add_argument("--workers", type=int, help="Concurrencia predeterminada de los escaneos.")
    command.add_argument("--timeout", type=float, help="Timeout predeterminado por operación de red.")
    command.add_argument("--max-hosts", type=int, help="Máximo de hosts autorizado por escaneo.")
    command.add_argument("--database", metavar="ARCHIVO", help="Ruta del inventario de elementos.")
    command.add_argument("--groups", metavar="ARCHIVO", help="Ruta de la base de grupos.")
    command.add_argument("--log", metavar="DIRECTORIO", help="Directorio de registros.")
    command.add_argument(
        "--projects-directory",
        metavar="DIRECTORIO",
        help="Carpeta predeterminada para nombres de proyecto VLF relativos.",
    )
    command.add_argument(
        "-log-cleanup",
        "--log-cleanup",
        choices=("on", "off"),
        help="Activa o desactiva la limpieza automática de logs antiguos.",
    )
    command.add_argument(
        "-log-retention-days",
        "--log-retention-days",
        type=int,
        metavar="DÍAS",
        help="Días durante los que se conservan los archivos de log.",
    )
    command.set_defaults(handler=run_settings)


def run_settings(args: argparse.Namespace) -> int:
    config = load_config()
    if (
        args.network_range is None
        and args.list_fields is None
        and args.dhcp_range is None
        and args.credentials is None
        and args.discovery is None
        and args.scan_profile is None
        and args.progress is None
        and args.service_identification is None
        and args.workers is None
        and args.timeout is None
        and args.max_hosts is None
        and args.database is None
        and args.groups is None
        and args.log is None
        and args.projects_directory is None
        and args.log_cleanup is None
        and args.log_retention_days is None
    ):
        print(json.dumps(config, indent=2, ensure_ascii=False))
        print(f"\nArchivo: {CONFIG_PATH.resolve()}")
        return 0

    changes: list[str] = []
    if args.network_range is not None:
        try:
            network = ipaddress.ip_network(args.network_range, strict=False)
        except ValueError as error:
            raise ValueError(f"rango CIDR no válido: {args.network_range}") from error
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError("el rango de red debe ser IPv4")
        config["range"] = args.network_range
        changes.append(f"Rango: {args.network_range}")
    if args.list_fields is not None:
        config["listColumns"] = normalize_columns(args.list_fields)
        changes.append(f"Columnas list: {', '.join(config['listColumns'])}")
    if args.dhcp_range is not None:
        config["dhcpRange"] = normalize_dhcp_range(args.dhcp_range)
        shown = config["dhcpRange"] or "sin configurar"
        changes.append(f"Rango DHCP: {shown}")
    if args.credentials is not None:
        path = args.credentials.strip()
        if not path:
            raise ValueError("la ruta de credenciales no puede estar vacía")
        config["credentials"] = path
        changes.append(f"Credenciales: {path}")
    if args.discovery is not None:
        config["discovery"] = args.discovery
        changes.append(f"Descubrimiento: {args.discovery}")
    if args.scan_profile is not None:
        config["scanProfile"] = args.scan_profile
        changes.append(f"Perfil de escaneo: {args.scan_profile}")
    if args.progress is not None:
        config["progress"] = args.progress == "on"
        changes.append(f"Progreso: {args.progress}")
    if args.service_identification is not None:
        config["serviceIdentification"] = args.service_identification == "on"
        changes.append(f"Identificación de servicios: {args.service_identification}")
    if args.workers is not None:
        if args.workers < 1:
            raise ValueError("workers debe ser mayor que cero")
        config["workers"] = args.workers
        changes.append(f"Workers: {args.workers}")
    if args.timeout is not None:
        if args.timeout <= 0:
            raise ValueError("timeout debe ser mayor que cero")
        config["timeout"] = args.timeout
        changes.append(f"Timeout: {args.timeout}")
    if args.max_hosts is not None:
        if args.max_hosts < 1:
            raise ValueError("max-hosts debe ser mayor que cero")
        config["maxHosts"] = args.max_hosts
        changes.append(f"Máximo de hosts: {args.max_hosts}")
    for argument, key, label in (
        (args.database, "database", "Base de elementos"),
        (args.groups, "groups", "Base de grupos"),
        (args.log, "log", "Directorio de logs"),
        (args.projects_directory, "projectsDirectory", "Directorio de proyectos"),
    ):
        if argument is not None:
            value = argument.strip()
            if not value:
                raise ValueError(f"{label} no puede quedar vacío")
            if key == "projectsDirectory" and value.casefold() in ("default", "auto"):
                value = r"%USERPROFILE%\Documents\LanCTL"
            config[key] = value
            changes.append(f"{label}: {value}")

    if args.log_cleanup is not None:
        config["logCleanupEnabled"] = args.log_cleanup == "on"
        state = "activada" if config["logCleanupEnabled"] else "desactivada"
        changes.append(f"Limpieza automática de logs: {state}")
    if args.log_retention_days is not None:
        if args.log_retention_days < 1:
            raise ValueError("la retención de logs debe ser de al menos 1 día")
        config["logRetentionDays"] = args.log_retention_days
        changes.append(f"Retención de logs: {args.log_retention_days} días")

    path = save_config(config)
    ok("CONFIGURADO", "\n".join((*changes, f"Archivo: {path}")))
    return 0
