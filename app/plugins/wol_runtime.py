from __future__ import annotations

import ipaddress
import socket
import time


def validate_mac(mac: str) -> bytes:
    clean = str(mac).strip().replace("-", ":").upper()
    parts = clean.split(":")
    try:
        raw = bytes(int(part, 16) for part in parts)
    except (ValueError, TypeError) as error:
        raise ValueError("MAC no válida para Wake-on-LAN") from error
    if len(parts) != 6 or len(raw) != 6 or raw in {b"\0" * 6, b"\xff" * 6} or raw[0] & 1:
        raise ValueError("MAC unicast no válida para Wake-on-LAN")
    return raw


def magic_packet(mac: str) -> bytes:
    raw = validate_mac(mac)
    return b"\xff" * 6 + raw * 16


def send_magic_packet(
    mac: str,
    broadcast: str = "255.255.255.255",
    port: int = 9,
    repeat: int = 3,
    interval: float = 0.5,
    interface: str | None = None,
    socket_factory=socket.socket,
    sleeper=time.sleep,
) -> int:
    address = ipaddress.ip_address(broadcast)
    if not isinstance(address, ipaddress.IPv4Address):
        raise ValueError("broadcast debe ser IPv4")
    if not 1 <= int(port) <= 65535:
        raise ValueError("puerto fuera de 1..65535")
    if not 1 <= int(repeat) <= 20:
        raise ValueError("repeat debe estar entre 1 y 20")
    if not 0 <= float(interval) <= 10:
        raise ValueError("interval debe estar entre 0 y 10 segundos")
    packet = magic_packet(mac)
    sock = socket_factory(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        if interface:
            sock.bind((str(ipaddress.ip_address(interface)), 0))
        for index in range(int(repeat)):
            sock.sendto(packet, (str(address), int(port)))
            if index + 1 < int(repeat):
                sleeper(float(interval))
    finally:
        sock.close()
    return int(repeat)
