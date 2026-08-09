from __future__ import annotations

import ctypes
import ipaddress
import platform
import random
import re
import socket
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import perf_counter

from app.models import Device
from app.services.manufacturer import detect_manufacturer
from app.services.network_discovery import discover_services

Network = ipaddress.IPv4Network
MAC_PATTERN = r"(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}"
DISCOVERY_MODES = ("icmp", "arp", "hybrid")
SCAN_ORDERS = ("ascending", "descending", "random")


def active_arp_mac(ip: str, timeout: float = 1.0) -> str:
    """Pregunta activamente por una IPv4 local sin confiar en la caché ARP."""
    if platform.system() == "Windows":
        destination = ctypes.windll.ws2_32.inet_addr(ip.encode("ascii"))
        mac = (ctypes.c_ubyte * 6)()
        length = ctypes.c_ulong(6)
        result = ctypes.windll.iphlpapi.SendARP(
            destination, 0, ctypes.byref(mac), ctypes.byref(length)
        )
        if result != 0 or length.value < 6:
            return ""
        return ":".join(f"{mac[index]:02X}" for index in range(6))

    try:
        result = subprocess.run(
            ["arping", "-c", "1", "-w", str(max(1, round(timeout))), ip],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout + 2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    match = re.search(MAC_PATTERN, result.stdout)
    return match.group(0).replace("-", ":").upper() if match else ""


def local_ipv4() -> ipaddress.IPv4Address:
    """Obtiene la IPv4 usada por la ruta de salida sin enviar datos."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return ipaddress.IPv4Address(sock.getsockname()[0])
    except OSError:
        try:
            return ipaddress.IPv4Address(socket.gethostbyname(socket.gethostname()))
        except (OSError, ipaddress.AddressValueError) as error:
            raise OSError("no se pudo detectar la dirección IPv4 local") from error
    finally:
        sock.close()


def resolve_network(value: str | None) -> Network:
    if value:
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError as error:
            raise ValueError(f"red CIDR no válida: {value}") from error
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError("por ahora el escaneo LAN solo admite redes IPv4")
        return network

    # /24 es una suposición conservadora y explícita cuando se desconoce la
    # máscara real de la red local.
    return ipaddress.IPv4Network(f"{local_ipv4()}/24", strict=False)


class LanScanner:
    def __init__(
        self,
        network: Network,
        workers: int,
        timeout: float,
        max_hosts: int,
        scan_order: str = "ascending",
    ):
        scan_order = scan_order.casefold()
        if scan_order not in SCAN_ORDERS:
            raise ValueError(
                f"orden de escaneo no válido: {scan_order}. Disponibles: {', '.join(SCAN_ORDERS)}"
            )
        self.network = network
        self.workers = workers
        self.timeout = timeout
        self.max_hosts = max_hosts
        self.scan_order = scan_order
        self.discovery_methods: dict[str, set[str]] = {}
        self.confirmed_devices: set[str] = set()
        self.response_times_ms: dict[str, dict[str, float]] = {}

    def _ordered_hosts(self) -> list[ipaddress.IPv4Address]:
        hosts = list(self.network.hosts())
        if self.scan_order == "descending":
            hosts.reverse()
        elif self.scan_order == "random":
            random.shuffle(hosts)
        return hosts

    @staticmethod
    def _timed(function, *args):
        started = perf_counter()
        result = function(*args)
        return result, (perf_counter() - started) * 1000

    def _parallel(self, function, values, phase: str, progress=None, found_key=None):
        values = list(values)
        if progress:
            progress.phase(phase)
        results = [None] * len(values)
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {
                executor.submit(function, value): index for index, value in enumerate(values)
            }
            for future in as_completed(futures):
                index = futures[future]
                result = future.result()
                results[index] = result
                if progress and found_key:
                    keys = found_key(values[index], result)
                    if isinstance(keys, tuple):
                        progress.found(*keys)
                    elif keys:
                        progress.found(keys)
                if progress:
                    progress.advance()
        return results

    def _parallel_discovery(
        self,
        hosts: list[str],
        use_icmp: bool,
        use_arp: bool,
        progress=None,
    ) -> tuple[set[str], dict[str, str]]:
        """Ejecuta la primera ronda ICMP y ARP en un solo pool acotado."""
        if progress:
            progress.phase("Descubrimiento ICMP + ARP")

        alive: set[str] = set()
        arp_macs: dict[str, str] = {}
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {}
            # Los trabajos se intercalan por host: ARP puede avanzar mientras
            # el ping del mismo host espera, compartiendo el mismo límite.
            for ip in hosts:
                if use_icmp:
                    futures[executor.submit(self._timed, self._ping, ip)] = ("icmp", ip)
                if use_arp:
                    futures[executor.submit(self._timed, active_arp_mac, ip, self.timeout)] = (
                        "arp",
                        ip,
                    )

            for future in as_completed(futures):
                method, ip = futures[future]
                result, elapsed_ms = future.result()
                found = bool(result)
                if method == "icmp" and found:
                    alive.add(ip)
                elif method == "arp" and found:
                    arp_macs[ip] = result
                if found:
                    self.response_times_ms.setdefault(ip, {})[method] = elapsed_ms
                if progress and found:
                    if method == "arp":
                        progress.found(ip, result)
                    else:
                        progress.found(ip)
                if progress:
                    progress.advance()
        return alive, arp_macs

    def response_time_for(self, device: Device) -> float | None:
        timings = self.response_times_ms.get(device.ip, {})
        # ICMP representa mejor la latencia. ARP queda como alternativa para
        # equipos que bloquean ping pero responden en la red local.
        return timings.get("icmp", timings.get("arp"))

    def _mark_discovery(self, ip: str, mac: str, method: str, confirmed: bool = True) -> None:
        self.discovery_methods.setdefault(f"ip:{ip}", set()).add(method)
        if mac:
            self.discovery_methods.setdefault(f"mac:{mac.upper()}", set()).add(method)
        if confirmed:
            self.confirmed_devices.add(f"ip:{ip}")
            if mac:
                self.confirmed_devices.add(f"mac:{mac.upper()}")

    def discovery_for(self, device: Device) -> str:
        methods = set(self.discovery_methods.get(f"ip:{device.ip}", set()))
        if device.mac:
            methods.update(self.discovery_methods.get(f"mac:{device.mac.upper()}", set()))
        order = ("ICMP", "ARP", "MDNS", "SSDP", "WSD", "LOCAL", "BASIC", "CACHE")
        return "+".join(method for method in order if method in methods) or "-"

    def is_confirmed(self, device: Device) -> bool:
        return f"ip:{device.ip}" in self.confirmed_devices or bool(
            device.mac and f"mac:{device.mac.upper()}" in self.confirmed_devices
        )

    def _retry_icmp(self, host_strings, attempts, active_ips, progress):
        for attempt in range(1, attempts):
            current = self._parallel(
                lambda ip: self._timed(self._ping, ip),
                host_strings,
                f"ICMP {attempt + 1}/{attempts}",
                progress,
                found_key=lambda ip, outcome: ip if outcome[0] else "",
            )
            for ip, (responded, elapsed_ms) in zip(host_strings, current):
                if responded:
                    active_ips.add(ip)
                    self.response_times_ms.setdefault(ip, {})["icmp"] = elapsed_ms

    def _discover_extra_services(self, extra_methods, attempts, active_arp, progress):
        if progress and extra_methods:
            progress.phase("Servicios LAN")
        findings = (
            discover_services(extra_methods, max(0.3, self.timeout * attempts))
            if extra_methods
            else {}
        )
        ips = {ip for ip in findings if ipaddress.IPv4Address(ip) in self.network}
        if progress and extra_methods:
            for ip in ips:
                progress.found(ip)
            progress.advance(len(extra_methods))

        missing = [ip for ip in ips if ip not in active_arp]
        if missing:
            macs = self._parallel(
                lambda ip: active_arp_mac(ip, self.timeout), missing, "ARP servicios", None
            )
            active_arp.update({ip: mac for ip, mac in zip(missing, macs) if mac})
        return findings, ips

    def _cached_ips(self, arp_entries, active_ips, active_arp, include_arp_cache):
        if not include_arp_cache:
            return set()
        live_macs = {mac.upper() for mac in active_arp.values() if mac} | {
            arp_entries[ip].upper() for ip in active_ips if arp_entries.get(ip)
        }
        return {
            ip
            for ip, mac in arp_entries.items()
            if ipaddress.IPv4Address(ip) in self.network
            and mac != "00:00:00:00:00:00"
            # Una IP antigua nunca desplaza la IP confirmada de la misma MAC.
            and (ip in active_ips or ip in active_arp or mac.upper() not in live_macs)
        }

    def _discovery_records(
        self,
        active_ips,
        active_arp,
        cached_ips,
        extra_ips,
        extra_findings,
        arp_entries,
        include_unknown,
        include_arp_cache,
    ):
        discovered = active_ips | set(active_arp) | cached_ips | extra_ips
        records = [
            self._make_record(ip, active_arp.get(ip, arp_entries.get(ip, "")))
            for ip in sorted(discovered, key=ipaddress.IPv4Address)
            if include_unknown or active_arp.get(ip) or ip in arp_entries
        ]
        for record in records:
            if record.ip in active_ips:
                self._mark_discovery(record.ip, record.mac, "ICMP")
            if record.ip in active_arp:
                self._mark_discovery(record.ip, record.mac, "ARP")
            for method in extra_findings.get(record.ip, set()):
                self._mark_discovery(record.ip, record.mac, method)
            if (
                include_arp_cache
                and record.ip in cached_ips
                and record.ip not in active_ips
                and record.ip not in active_arp
            ):
                self._mark_discovery(record.ip, record.mac, "CACHE", confirmed=False)
        return records

    def _include_local_device(self, records):
        # El equipo local no aparece en su propia caché ARP.
        own_ip = str(local_ipv4())
        if ipaddress.IPv4Address(own_ip) not in self.network:
            return
        own_mac = self._local_mac(own_ip)
        existing = next((record for record in records if record.ip == own_ip), None)
        if existing and own_mac:
            existing.mac = own_mac
        elif existing is None:
            records.append(self._make_record(own_ip, own_mac))
        self._mark_discovery(own_ip, own_mac, "LOCAL")

    def _include_special_devices(self, records, arp_entries):
        gateway = str(next(self.network.hosts(), self.network.network_address))
        broadcast = str(self.network.broadcast_address)
        special = {
            gateway: self._make_record(
                gateway,
                arp_entries.get(gateway, ""),
                "GATEWAY",
                cnf="O",
                description="Puerta de enlace de la red",
                groups=["BASIC"],
            ),
            broadcast: self._make_record(
                broadcast,
                "FF:FF:FF:FF:FF:FF",
                "BRODCAST",
                cnf="O",
                description="Difusion general de la LAN",
                groups=["BASIC"],
            ),
        }
        by_ip = {record.ip: record for record in records}
        for ip, record in special.items():
            if ip not in by_ip:
                by_ip[ip] = record
                self._mark_discovery(ip, record.mac, "BASIC")
                continue
            existing = by_ip[ip]
            existing.alias = record.alias
            existing.default_alias = record.default_alias
            existing.description = record.description
            existing.groups = list(dict.fromkeys([*existing.groups, *record.groups]))
            if record.mac:
                existing.mac = record.mac
        return sorted(by_ip.values(), key=lambda item: ipaddress.IPv4Address(item.ip))

    def _enrich_records(self, records, resolve_names, host_count, progress):
        if resolve_names:
            original_workers = self.workers
            self.workers = min(self.workers, 32)
            try:
                names = self._parallel(
                    self._resolve_name,
                    (record.ip for record in records),
                    "Nombres DNS",
                    progress,
                )
            finally:
                self.workers = original_workers
            for record, name in zip(records, names):
                record.default_name = name
            if progress and len(records) < host_count:
                progress.advance(host_count - len(records))
        for record in records:
            record.manufacturer = detect_manufacturer(record.mac)

    def scan(
        self,
        include_unknown: bool = False,
        resolve_names: bool = True,
        discovery: str = "icmp",
        include_arp_cache: bool = False,
        attempts: int = 1,
        extra_methods: tuple[str, ...] = (),
        progress=None,
        registered_total: int = 0,
        registered_identities: dict[str, str] | None = None,
    ) -> list[Device]:
        discovery = discovery.casefold()
        if discovery not in DISCOVERY_MODES:
            raise ValueError(
                f"método de descubrimiento no válido: {discovery}. "
                f"Disponibles: {', '.join(DISCOVERY_MODES)}"
            )
        self.discovery_methods = {}
        self.confirmed_devices = set()
        self.response_times_ms = {}
        attempts = max(1, attempts)
        hosts = self._ordered_hosts()
        if len(hosts) > self.max_hosts:
            raise ValueError(
                f"la red contiene {len(hosts)} hosts; usa --max-hosts para autorizarla"
            )

        host_strings = [str(host) for host in hosts]
        progress_total = (
            (len(host_strings) * attempts if discovery in ("icmp", "hybrid") else 0)
            + (len(host_strings) if discovery in ("arp", "hybrid") else 0)
            + len(extra_methods)
            + (len(host_strings) if resolve_names else 0)
        )
        if progress:
            progress.begin(
                progress_total,
                found_total=registered_total,
                known_identities=registered_identities,
            )
        use_icmp = discovery in ("icmp", "hybrid")
        use_arp = discovery in ("arp", "hybrid")
        active_ips, active_arp = self._parallel_discovery(host_strings, use_icmp, use_arp, progress)
        # Las rondas posteriores siguen siendo reintentos reales, pero la
        # primera ronda ICMP y ARP ya no tiene que esperar una fase completa.
        if use_icmp:
            self._retry_icmp(host_strings, attempts, active_ips, progress)

        extra_findings, extra_ips = self._discover_extra_services(
            extra_methods, attempts, active_arp, progress
        )

        arp_entries = self._read_arp_table()
        cached_ips = self._cached_ips(arp_entries, active_ips, active_arp, include_arp_cache)
        records = self._discovery_records(
            active_ips,
            active_arp,
            cached_ips,
            extra_ips,
            extra_findings,
            arp_entries,
            include_unknown,
            include_arp_cache,
        )

        self._include_local_device(records)
        records = self._include_special_devices(records, arp_entries)
        self._enrich_records(records, resolve_names, len(host_strings), progress)
        if progress:
            progress.complete()
        return records

    @staticmethod
    def _make_record(
        ip: str,
        mac: str,
        alias: str = "",
        cnf: str = "X",
        description: str = "-",
        groups: list[str] | None = None,
    ) -> Device:
        return Device(
            ip=ip,
            cnf=cnf,
            mac=mac,
            alias=alias,
            default_alias=alias,
            description=description,
            groups=groups or [],
        )

    def _resolve_name(self, ip: str) -> str:
        if ip == str(self.network.broadcast_address):
            return ""
        if platform.system() == "Windows":
            command = [
                "ping",
                "-a",
                "-n",
                "1",
                "-w",
                str(max(100, int(self.timeout * 1000))),
                ip,
            ]
        else:
            command = ["getent", "hosts", ip]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=self.timeout + 1,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""

        if platform.system() == "Windows":
            match = re.search(
                rf"(?:Pinging|ping\s+a)\s+([^\s\[]+)\s+\[{re.escape(ip)}\]",
                result.stdout,
                re.IGNORECASE,
            )
            return match.group(1).rstrip(".") if match else ""

        parts = result.stdout.split()
        return parts[1].rstrip(".") if len(parts) >= 2 else ""

    @staticmethod
    def _local_mac(ip: str) -> str:
        if platform.system() == "Windows":
            script = (
                "$a=Get-NetIPAddress -AddressFamily IPv4 "
                f"-IPAddress '{ip}' -ErrorAction SilentlyContinue | "
                "Select-Object -First 1; "
                "if($a){(Get-NetAdapter -InterfaceIndex $a.InterfaceIndex "
                "-ErrorAction SilentlyContinue).MacAddress}"
            )
            command = [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                script,
            ]
        else:
            command = ["ip", "-o", "link"]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ""

        match = re.search(MAC_PATTERN, result.stdout)
        return match.group(0).replace("-", ":").upper() if match else ""

    def _ping(self, ip: str) -> bool:
        milliseconds = max(1, int(self.timeout * 1000))
        if platform.system() == "Windows":
            command = ["ping", "-n", "1", "-w", str(milliseconds), ip]
        else:
            seconds = max(1, round(self.timeout))
            command = ["ping", "-c", "1", "-W", str(seconds), ip]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout + 1,
                check=False,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def _read_arp_table(self) -> dict[str, str]:
        try:
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                errors="replace",
                timeout=10,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            raise OSError("no se pudo consultar la tabla ARP del sistema") from error

        entries: dict[str, str] = {}
        for line in result.stdout.splitlines():
            ip_match = re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line)
            mac_match = re.search(MAC_PATTERN, line)
            if not ip_match or not mac_match:
                continue
            ip = ip_match.group(0)
            try:
                address = ipaddress.IPv4Address(ip)
            except ipaddress.AddressValueError:
                continue
            if address not in self.network:
                continue
            entries[ip] = mac_match.group(0).replace("-", ":").upper()
        return entries
