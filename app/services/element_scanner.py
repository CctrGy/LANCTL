from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import platform
import re
import socket
import subprocess
from time import monotonic
from typing import Callable


COMMON_PORTS = (
    20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 81, 110, 123, 135, 137,
    138, 139, 143, 161, 162, 389, 443, 445, 465, 500, 515, 548, 554,
    587, 631, 636, 993, 995, 1433, 1723, 1883, 1900, 2049, 3306, 3389,
    5000, 5060, 5353, 5432, 5900, 8000, 8080, 8081, 8443, 8883, 9100,
)

SERVICE_NAMES = {
    20: "ftp-data", 21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp",
    53: "dns", 67: "dhcp-server", 68: "dhcp-client", 69: "tftp",
    80: "http", 110: "pop3", 123: "ntp", 135: "msrpc", 139: "netbios",
    143: "imap", 161: "snmp", 389: "ldap", 443: "https", 445: "smb",
    515: "printer", 548: "afp", 554: "rtsp", 631: "ipp", 636: "ldaps",
    993: "imaps", 995: "pop3s", 1433: "mssql", 1883: "mqtt",
    2049: "nfs", 3306: "mysql", 3389: "rdp", 5000: "upnp/http",
    5432: "postgresql", 5900: "vnc", 8000: "http-alt", 8080: "http-proxy",
    8443: "https-alt", 8883: "mqtts", 9100: "printer-raw",
}


@dataclass(frozen=True)
class OpenPort:
    port: int
    service: str
    banner: str = ""


@dataclass
class ElementScanResult:
    ip: str
    reachable: bool
    latency_ms: float | None
    ttl: int | None
    hostname: str
    observed_mac: str
    scanned_ports: int
    open_ports: list[OpenPort] = field(default_factory=list)
    duration: float = 0.0


def parse_ports(value: str, max_ports: int = 4096) -> list[int]:
    if value.strip().casefold() in ("common", "default"):
        return list(COMMON_PORTS)
    ports: set[int] = set()
    for raw_part in value.split(","):
        part = raw_part.strip()
        if not part:
            continue
        try:
            if "-" in part:
                raw_start, raw_end = part.split("-", 1)
                start, end = int(raw_start), int(raw_end)
                if start > end:
                    raise ValueError
                ports.update(range(start, end + 1))
            else:
                ports.add(int(part))
        except ValueError as error:
            raise ValueError(f"lista de puertos no válida: {value}") from error
    if not ports or min(ports) < 1 or max(ports) > 65535:
        raise ValueError("los puertos deben estar entre 1 y 65535")
    if len(ports) > max_ports:
        raise ValueError(
            f"se solicitaron {len(ports)} puertos; usa --all-ports para un barrido completo"
        )
    return sorted(ports)


def _service(port: int) -> str:
    if port in SERVICE_NAMES:
        return SERVICE_NAMES[port]
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return "unknown"


def _sanitize_banner(value: bytes) -> str:
    text = value.decode("utf-8", errors="replace")
    return " ".join(text.split())[:120]


def scan_tcp_ports(
    host: str,
    ports: list[int],
    timeout: float,
    workers: int,
    banners: bool = False,
    connector: Callable = socket.create_connection,
) -> list[OpenPort]:
    def inspect(port: int) -> OpenPort | None:
        try:
            connection = connector((host, port), timeout=timeout)
            try:
                banner = ""
                if banners:
                    connection.settimeout(timeout)
                    try:
                        banner = _sanitize_banner(connection.recv(256))
                    except (OSError, socket.timeout):
                        pass
                return OpenPort(port, _service(port), banner)
            finally:
                connection.close()
        except OSError:
            return None

    with ThreadPoolExecutor(max_workers=min(workers, len(ports))) as executor:
        return [finding for finding in executor.map(inspect, ports) if finding]


def ping_details(host: str, timeout: float) -> tuple[bool, float | None, int | None]:
    milliseconds = max(1, int(timeout * 1000))
    command = (
        ["ping", "-n", "1", "-w", str(milliseconds), host]
        if platform.system() == "Windows"
        else ["ping", "-c", "1", "-W", str(max(1, round(timeout))), host]
    )
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, errors="replace",
            timeout=timeout + 2, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, None, None
    latency = re.search(r"(?:time|tiempo)[=<]\s*([0-9.]+)\s*ms", result.stdout, re.I)
    ttl = re.search(r"ttl[= ](\d+)", result.stdout, re.I)
    return (
        result.returncode == 0,
        float(latency.group(1)) if latency else None,
        int(ttl.group(1)) if ttl else None,
    )


def observed_arp_mac(host: str) -> str:
    try:
        result = subprocess.run(
            ["arp", "-a", host], capture_output=True, text=True,
            errors="replace", timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    match = re.search(r"(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}", result.stdout, re.I)
    return match.group(0).replace("-", ":").upper() if match else ""


def reverse_hostname(host: str, timeout: float) -> str:
    if platform.system() != "Windows":
        command = ["getent", "hosts", host]
    else:
        command = ["ping", "-a", "-n", "1", "-w", str(max(1, int(timeout * 1000))), host]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, errors="replace",
            timeout=timeout + 2, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if platform.system() == "Windows":
        match = re.search(rf"(?:Pinging|ping\s+a)\s+([^\s\[]+)\s+\[{re.escape(host)}\]", result.stdout, re.I)
        return match.group(1).rstrip(".") if match else ""
    parts = result.stdout.split()
    return parts[1].rstrip(".") if len(parts) >= 2 else ""


class ElementScanner:
    def __init__(self, timeout: float = 0.5, workers: int = 128):
        if timeout <= 0 or workers < 1:
            raise ValueError("timeout y workers deben ser mayores que cero")
        self.timeout = timeout
        self.workers = workers

    def scan(self, host: str, ports: list[int], banners: bool = False) -> ElementScanResult:
        started = monotonic()
        reachable, latency, ttl = ping_details(host, self.timeout)
        open_ports = scan_tcp_ports(host, ports, self.timeout, self.workers, banners)
        return ElementScanResult(
            ip=host,
            reachable=reachable or bool(open_ports),
            latency_ms=latency,
            ttl=ttl,
            hostname=reverse_hostname(host, self.timeout),
            observed_mac=observed_arp_mac(host),
            scanned_ports=len(ports),
            open_ports=open_ports,
            duration=monotonic() - started,
        )
