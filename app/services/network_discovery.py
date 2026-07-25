from __future__ import annotations

import select
import socket
import struct
import time
import uuid


EXTRA_DISCOVERY_METHODS = ("mdns", "ssdp", "wsd")


def _dns_name(value: str) -> bytes:
    return b"".join(bytes((len(part),)) + part.encode("ascii") for part in value.split(".")) + b"\0"


def discovery_probe(method: str) -> tuple[bytes, tuple[str, int]]:
    method = method.casefold()
    if method == "ssdp":
        payload = (
            "M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\n"
            'MAN: "ssdp:discover"\r\nMX: 1\r\nST: ssdp:all\r\n\r\n'
        ).encode("ascii")
        return payload, ("239.255.255.250", 1900)
    if method == "mdns":
        # QCLASS con bit QU solicita respuesta unicast al puerto efímero.
        question = _dns_name("_services._dns-sd._udp.local") + struct.pack("!HH", 12, 0x8001)
        return struct.pack("!HHHHHH", 0, 0, 1, 0, 0, 0) + question, ("224.0.0.251", 5353)
    if method == "wsd":
        message_id = f"urn:uuid:{uuid.uuid4()}"
        payload = f'''<?xml version="1.0" encoding="UTF-8"?>
<e:Envelope xmlns:e="http://www.w3.org/2003/05/soap-envelope"
 xmlns:w="http://schemas.xmlsoap.org/ws/2004/08/addressing"
 xmlns:d="http://schemas.xmlsoap.org/ws/2005/04/discovery">
 <e:Header><w:MessageID>{message_id}</w:MessageID>
 <w:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</w:To>
 <w:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</w:Action></e:Header>
 <e:Body><d:Probe/></e:Body></e:Envelope>'''.encode("utf-8")
        return payload, ("239.255.255.250", 3702)
    raise ValueError(f"método de descubrimiento adicional no válido: {method}")


def multicast_discover(methods: tuple[str, ...], timeout: float) -> dict[str, set[str]]:
    """Devuelve IP de emisores que responden a sondas estándar de descubrimiento."""
    sockets: dict[socket.socket, str] = {}
    findings: dict[str, set[str]] = {}
    try:
        for method in dict.fromkeys(item.casefold() for item in methods):
            payload, destination = discovery_probe(method)
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setblocking(False)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.sendto(payload, destination)
            sockets[sock] = method.upper()
        deadline = time.monotonic() + max(0.1, timeout)
        while sockets and time.monotonic() < deadline:
            readable, _, _ = select.select(
                list(sockets), [], [], max(0.0, deadline - time.monotonic())
            )
            if not readable:
                break
            for sock in readable:
                try:
                    _payload, address = sock.recvfrom(65535)
                except OSError:
                    continue
                findings.setdefault(address[0], set()).add(sockets[sock])
    except OSError:
        return findings
    finally:
        for sock in sockets:
            sock.close()
    return findings
