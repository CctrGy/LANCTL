from __future__ import annotations

import ipaddress
import socket


def validate_endpoint(bind, cidr, port, *, interfaces=None):
    # Los comodines aparecen aquí para rechazarlos, nunca para abrir un socket.
    if not bind or bind in {"0.0.0.0", "::", "localhost"}:  # nosec B104
        raise ValueError("bind debe ser una IPv4 LAN explícita")
    address = ipaddress.ip_address(bind)
    network = ipaddress.ip_network(cidr, strict=False)
    if address.version != 4 or network.version != 4 or address not in network:
        raise ValueError("bind no pertenece al CIDR LAN permitido")
    if not 1 <= int(port) <= 65535:
        raise ValueError("puerto fuera de 1..65535")
    if interfaces is not None and str(address) not in interfaces:
        raise ValueError("bind no corresponde a una interfaz local")
    return str(address), str(network), int(port)


def source_allowed(source, cidr):
    try:
        return ipaddress.ip_address(source) in ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False


def port_available(bind, port):
    sock = socket.socket()
    try:
        sock.bind((bind, port))
        return True
    except OSError:
        return False
    finally:
        sock.close()
