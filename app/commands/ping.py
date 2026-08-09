from __future__ import annotations

import argparse
import ipaddress
import json
import os
import sys

from colorama import Fore, Style

from app.core.config import load_config
from app.core.database import DeviceDatabase
from app.core.logger import write_log
from app.services.element_scanner import observed_arp_mac, ping_details
from app.services.lan_scanner import active_arp_mac

PING_METHODS = ("auto", "ping", "arp")


def register_ping_command(commands: argparse._SubParsersAction) -> None:
    config = load_config()
    command = commands.add_parser(
        "ping",
        help="Comprueba puntualmente si un elemento responde por PING o ARP.",
        description=(
            "Diagnostica un único elemento sin modificar la base de datos. "
            "PING prueba ICMP; ARP realiza una consulta activa en la LAN; "
            "AUTO combina ambos métodos."
        ),
    )
    command.add_argument("selector", help="IP, MAC, alias o nombre registrado.")
    method = command.add_mutually_exclusive_group()
    method.add_argument(
        "--method",
        choices=PING_METHODS,
        default="auto",
        help="Buscador utilizado: auto, ping o arp (por defecto: auto).",
    )
    method.add_argument(
        "--ping",
        dest="method",
        action="store_const",
        const="ping",
        help="Usa únicamente una solicitud ICMP.",
    )
    method.add_argument(
        "--arp",
        dest="method",
        action="store_const",
        const="arp",
        help="Usa únicamente una solicitud ARP activa.",
    )
    command.add_argument(
        "--timeout",
        type=float,
        default=config["timeout"],
        help="Tiempo máximo de cada comprobación, en segundos.",
    )
    command.add_argument("--json", action="store_true", help="Devuelve el diagnóstico como JSON.")
    command.add_argument(
        "--database", default=config["database"], help="Archivo JSON de elementos."
    )
    command.set_defaults(handler=run_ping)


def _resolve_target(database: DeviceDatabase, selector: str):
    try:
        return database.resolve(selector)
    except ValueError as original_error:
        try:
            matches = database.search(selector)
            if len(matches) == 1:
                return matches[0]
        except ValueError:
            pass
        try:
            ipaddress.IPv4Address(selector)
        except ipaddress.AddressValueError:
            raise original_error
        return None


def _paint(value: str, color: str) -> str:
    if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
        return value
    return f"{Style.BRIGHT}{color}{value}{Style.RESET_ALL}"


def run_ping(args: argparse.Namespace) -> int:
    if args.timeout <= 0:
        raise ValueError("--timeout debe ser mayor que cero")
    database = DeviceDatabase(args.database)
    device = _resolve_target(database, args.selector)
    ip = device.ip if device else args.selector
    if not ip or ip == "-":
        raise ValueError(f"{args.selector} no tiene una IP que se pueda comprobar")

    ping_ok, latency, ttl = (False, None, None)
    arp_mac = ""
    if args.method in ("auto", "ping"):
        ping_ok, latency, ttl = ping_details(ip, args.timeout)
    if args.method in ("auto", "arp"):
        arp_mac = active_arp_mac(ip, args.timeout)
    elif ping_ok:
        # Una sonda ICMP suele poblar la caché; se consulta sin generar otra.
        arp_mac = observed_arp_mac(ip)

    arp_ok = bool(arp_mac) if args.method in ("auto", "arp") else False
    detected = ping_ok or arp_ok
    expected_mac = device.mac if device else ""
    identity_match = (
        None if not expected_mac or not arp_mac else expected_mac.casefold() == arp_mac.casefold()
    )
    methods = [name for name, found in (("PING", ping_ok), ("ARP", arp_ok)) if found]
    payload = {
        "selector": args.selector,
        "ip": ip,
        "method": args.method,
        "detected": detected,
        "detectedBy": methods,
        "ping": {"responded": ping_ok, "latencyMs": latency, "ttl": ttl},
        "arp": {"responded": arp_ok, "mac": arp_mac},
        "expectedMac": expected_mac,
        "identityMatch": identity_match,
    }
    write_log(
        f"PING selector={args.selector} ip={ip} method={args.method} "
        f"detected={detected} by={'+'.join(methods) or '-'} mac={arp_mac or '-'}"
    )
    if detected and device is not None and methods:
        database.record_detection(device.mac or device.ip, methods)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        state = (
            _paint("DETECTADO", Fore.LIGHTGREEN_EX)
            if detected
            else _paint("NO DETECTADO", Fore.LIGHTRED_EX)
        )
        print(f"{_paint('CONEXIÓN', Fore.CYAN)} {args.selector}")
        print(f"  Estado       : {state}")
        print(f"  IP           : {_paint(ip, Fore.LIGHTBLUE_EX)}")
        print(f"  Buscador     : {args.method.upper()}")
        print(f"  Detectado por: {' + '.join(methods) or '-'}")
        print(f"  Latencia     : {f'{latency:.2f} ms' if latency is not None else '-'}")
        print(f"  TTL          : {ttl if ttl is not None else '-'}")
        print(f"  MAC observada: {_paint(arp_mac or '-', Fore.LIGHTMAGENTA_EX)}")
        if expected_mac:
            match = "SÍ" if identity_match else "NO" if identity_match is False else "-"
            print(f"  Identidad MAC: {match} | esperada {expected_mac}")
    return 0 if detected else 1
