from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
import sys

from colorama import Fore, Style

from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.logger import write_log
from app.core.layout import fit_text, terminal_columns, wrapped_lines
from app.services.element_scanner import ElementScanner, parse_ports
from app.services.manufacturer import detect_manufacturer


def register_scan_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "scan",
        help="Inspecciona en profundidad un único elemento de la LAN.",
        description=(
            "Resuelve un elemento por IP, MAC o alias y comprueba identidad, "
            "disponibilidad y puertos TCP. No modifica el dispositivo."
        ),
    )
    command.add_argument("selector", help="IP, MAC o alias registrado en LANCTL.")
    command.add_argument(
        "--ports", default="common", metavar="LISTA",
        help="Puertos o rangos: 22,80,443,8000-8100 (por defecto: common).",
    )
    command.add_argument(
        "--all-ports", action="store_true",
        help="Autoriza explícitamente el escaneo TCP 1-65535.",
    )
    command.add_argument("--timeout", type=float, default=0.5, help="Tiempo máximo por conexión, en segundos.")
    command.add_argument("--workers", type=int, default=128, help="Número máximo de conexiones simultáneas.")
    command.add_argument(
        "--banners", action="store_true",
        help="Lee banners pasivos; no envía sondas específicas de protocolo.",
    )
    command.add_argument("--json", action="store_true", help="Salida JSON.")
    command.add_argument("--database", default=config["database"], help="Archivo JSON de elementos.")
    command.set_defaults(handler=run_scan)


def _color(value: str, color: str) -> str:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return value
    return f"{Style.BRIGHT}{color}{value}{Style.RESET_ALL}"


def _shown(value) -> str:
    return "-" if value in (None, "", []) else str(value)


def run_scan(args: argparse.Namespace) -> int:
    device = DeviceDatabase(args.database).resolve(args.selector)
    if device.ip in ("", "-"):
        raise ValueError(f"{args.selector} no tiene una IP registrada que pueda escanearse")
    if args.all_ports and args.ports != "common":
        raise ValueError("usa --all-ports o --ports, pero no ambos")
    ports = list(range(1, 65536)) if args.all_ports else parse_ports(args.ports)
    scanner = ElementScanner(timeout=args.timeout, workers=args.workers)
    result = scanner.scan(device.ip, ports, banners=args.banners)
    manufacturer = device.manufacturer or detect_manufacturer(device.mac)
    identity_match = (
        None if not result.observed_mac or not device.mac
        else result.observed_mac.casefold() == device.mac.casefold()
    )
    write_log(
        f"SCAN element={device.device_id} ip={device.ip} reachable={result.reachable} "
        f"ports={result.scanned_ports} open={len(result.open_ports)}"
    )

    if args.json:
        payload = {
            "element": {
                "deviceId": device.device_id, "ip": device.ip, "mac": device.mac,
                "alias": device.alias, "name": device.name,
                "manufacturer": manufacturer, "groups": device.groups,
            },
            "observation": {**asdict(result), "identityMatch": identity_match},
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    state = _color("ACTIVO", Fore.LIGHTGREEN_EX) if result.reachable else _color("NO DETECTADO", Fore.LIGHTRED_EX)
    print(f"\n{_color('ELEMENTO', Fore.CYAN)}")
    print(f"  Estado       : {state}")
    print(f"  IP registrada: {_color(device.ip, Fore.LIGHTBLUE_EX)}")
    print(f"  MAC registrada: {_color(_shown(device.mac), Fore.LIGHTMAGENTA_EX)}")
    print(f"  MAC observada : {_shown(result.observed_mac)}")
    match_text = "Sí" if identity_match is True else "NO" if identity_match is False else "-"
    print(f"  Coincidencia  : {match_text}")
    print(f"  Alias / nombre: {_shown(device.alias)} / {_shown(device.name)}")
    print(f"  Fabricante    : {_shown(manufacturer)}")
    print(f"  Hostname      : {_shown(result.hostname or device.default_name)}")
    print(f"  Grupos        : {_shown(', '.join(device.groups))}")
    print(f"  Latencia / TTL: {_shown(result.latency_ms)} ms / {_shown(result.ttl)}")

    print(f"\n{_color('PUERTOS TCP ABIERTOS', Fore.CYAN)}")
    if result.open_ports:
        available = terminal_columns()
        banner_width = max(6, *(len(port.banner) for port in result.open_ports))
        if available:
            banner_width = max(6, min(banner_width, available - 29))
        print(f"  {'port':<5}  {'service':<16}  {'banner':<{banner_width}}")
        print(f"  {'-' * 5}  {'-' * 16}  {'-' * banner_width}")
        for port in result.open_ports:
            banner = fit_text(port.banner or "-", banner_width)
            print(f"  {_color(str(port.port).ljust(5), Fore.LIGHTGREEN_EX)}  {fit_text(port.service, 16):<16}  {banner}")
    else:
        print("  Ninguno detectado en el conjunto examinado.")
    summary = (
        f"Examinados: {result.scanned_ports} | Abiertos: {len(result.open_ports)} "
        f"| Duración: {result.duration:.2f} s"
    )
    for index, line in enumerate(
        wrapped_lines(summary, max(1, (terminal_columns() or 120) - 2))
    ):
        print(("\n  " if index == 0 else "  ") + line)
    if not args.all_ports:
        print("  Alcance: puertos habituales; usa --all-ports para 1-65535.")
    return 0 if result.reachable else 1
