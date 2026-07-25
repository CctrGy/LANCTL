from __future__ import annotations

import argparse
from datetime import datetime
import ipaddress

from app.core.config import load_config, normalize_dhcp_range, save_config
from app.core.console import ok
from app.core.credentials import CredentialStore
from app.core.database import DeviceDatabase
from app.core.tr064 import Tr064Client


def _add_download_arguments(command: argparse.ArgumentParser, *, gateway: bool) -> None:
    config = load_config()
    if gateway:
        command.add_argument(
            "gateway", nargs="?", default="GATEWAY", help="IP, MAC o alias del router."
        )
    else:
        command.set_defaults(gateway="GATEWAY")
    command.add_argument(
        "--port",
        type=int,
        default=int(config.get("tr064Port", 49000)),
        help="Puerto TR-064 del router.",
    )
    command.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Tiempo máximo de espera en segundos.",
    )
    command.add_argument(
        "--database",
        default=config["database"],
        help="Archivo JSON de elementos.",
    )
    command.add_argument(
        "--store",
        default=config["credentials"],
        help="Almacén cifrado de credenciales.",
    )
    command.set_defaults(handler=run_download_settings)


def register_gateway_command(commands: argparse._SubParsersAction) -> None:
    gateway = commands.add_parser(
        "GATEWAY",
        aliases=["gateway"],
        help="Consulta y configura el gateway mediante TR-064.",
    )
    actions = gateway.add_subparsers(dest="gateway_action", metavar="ACCIÓN")
    actions.required = True
    download = actions.add_parser(
        "downloadSettings",
        aliases=["downloadsettings", "download-settings"],
        help="Descarga las opciones LAN y DHCP interesantes para configuración.",
    )
    _add_download_arguments(download, gateway=False)


def register_download_settings_command(commands: argparse._SubParsersAction) -> None:
    """Compatibilidad con la ruta antigua: run downloadSettings."""
    command = commands.add_parser(
        "downloadSettings",
        aliases=["downloadsettings", "download-settings"],
        help="Alias heredado de «GATEWAY downloadSettings».",
    )
    _add_download_arguments(command, gateway=True)


def _first_address(value: str, fallback: str) -> str:
    candidates = value.replace(",", " ").split()
    return candidates[0] if candidates else fallback


def lan_settings(info: dict[str, str], gateway_ip: str, port: int) -> dict:
    router = _first_address(info.get("NewIPRouters", ""), gateway_ip)
    mask = info.get("NewSubnetMask", "").strip()
    if not mask:
        raise ValueError("TR-064 no ha devuelto la máscara de la red LAN")
    try:
        network = ipaddress.IPv4Network(f"{router}/{mask}", strict=False)
    except ValueError as error:
        raise ValueError("TR-064 ha devuelto una configuración IPv4 inválida") from error

    minimum = info.get("NewMinAddress", "").strip()
    maximum = info.get("NewMaxAddress", "").strip()
    dhcp_range = normalize_dhcp_range(f"{minimum}-{maximum}") if minimum and maximum else None
    enabled = info.get("NewDHCPServerEnable", "").strip().casefold()
    result = {
        "range": str(network),
        "gateway": router,
        "subnetMask": mask,
        "dhcpRange": dhcp_range,
        "dhcpEnabled": enabled in ("1", "true", "yes"),
        "dnsServers": [
            value for value in info.get("NewDNSServers", "").replace(",", " ").split() if value
        ],
        "domainName": info.get("NewDomainName", "").strip(),
        "reservedAddresses": [
            value
            for value in info.get("NewReservedAddresses", "").replace(",", " ").split()
            if value
        ],
        "tr064Host": gateway_ip,
        "tr064Port": port,
        "settingsDownloadedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    lease = info.get("NewDHCPLeaseTime", "").strip()
    if lease:
        try:
            result["dhcpLeaseTime"] = int(lease)
        except ValueError:
            result["dhcpLeaseTime"] = lease
    return result


def run_download_settings(args: argparse.Namespace) -> int:
    config = load_config()
    device = DeviceDatabase(args.database).resolve(args.gateway)
    reference = device.credentials.get("tr-064")
    if not reference:
        raise ValueError(
            f"{device.alias or device.ip} no tiene credenciales TR-064; ejecuta "
            f"run credential {device.alias or device.ip} set tr-064 -user USUARIO"
        )
    credential = CredentialStore(args.store).get(reference)
    client = Tr064Client(
        device.ip,
        credential["username"],
        credential["password"],
        port=args.port,
        timeout=args.timeout,
    )
    info = client.call("LANHostConfigManagement", "GetInfo")
    downloaded = lan_settings(info, device.ip, args.port)
    config.update(downloaded)
    path = save_config(config)
    dhcp = downloaded["dhcpRange"] or "desactivado/no publicado"
    ok(
        "DESCARGADO",
        "\n".join(
            (
                f"Red LAN: {downloaded['range']}",
                f"Gateway: {downloaded['gateway']}",
                f"DHCP: {dhcp}",
                f"Archivo: {path}",
            )
        ),
    )
    return 0
