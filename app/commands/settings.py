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
    command.set_defaults(handler=run_settings)


def run_settings(args: argparse.Namespace) -> int:
    config = load_config()
    if (
        args.network_range is None
        and args.list_fields is None
        and args.dhcp_range is None
        and args.credentials is None
        and args.discovery is None
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

    path = save_config(config)
    ok("CONFIGURADO", "\n".join((*changes, f"Archivo: {path}")))
    return 0
