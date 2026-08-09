from __future__ import annotations

import socket
from time import monotonic

from app.services.element_scanner import ping_details
from app.services.lan_scanner import active_arp_mac

from .models import CheckResult, CheckSpec


class CheckRegistry:
    def __init__(self):
        self._items = {}

    def register(self, spec: CheckSpec):
        if not spec.check_id or spec.check_id in self._items:
            raise ValueError("check ya registrado o sin id")
        if (
            not callable(spec.handler)
            or spec.minimum_interval < 5
            or not 0.05 <= spec.timeout <= 120
        ):
            raise ValueError("contrato de check no válido")
        self._items[spec.check_id] = spec
        return spec

    def get(self, check_id):
        try:
            return self._items[check_id]
        except KeyError as error:
            raise ValueError(f"check no registrado: {check_id}") from error

    def list(self):
        return list(self._items.values())

    def remove_owner(self, owner):
        self._items = {k: v for k, v in self._items.items() if v.owner != owner}


def availability(target, timeout=0.8) -> CheckResult:
    started = monotonic()
    ip = target.ip
    arp = bool(active_arp_mac(ip, timeout))
    ping, latency, _ttl = ping_details(ip, timeout)
    return CheckResult(
        "availability",
        target.device_id,
        arp or ping,
        latencyMs=latency,
        evidence=tuple(x for x, v in (("ARP", arp), ("ICMP", ping)) if v),
        metrics={"durationMs": int((monotonic() - started) * 1000)},
    )


def ping(target, timeout=0.8) -> CheckResult:
    success, latency, ttl = ping_details(target.ip, timeout)
    return CheckResult(
        "ping",
        target.device_id,
        success,
        latencyMs=latency,
        evidence=("ICMP",) if success else (),
        metrics={"ttl": ttl} if ttl is not None else {},
    )


def arp(target, timeout=0.8) -> CheckResult:
    mac = active_arp_mac(target.ip, timeout)
    return CheckResult(
        "arp",
        target.device_id,
        bool(mac),
        evidence=("ARP",) if mac else (),
        metrics={"observedMac": mac} if mac else {},
    )


def tcp_port(target, port, timeout=0.8) -> CheckResult:
    try:
        with socket.create_connection((target.ip, int(port)), timeout=timeout):
            success = True
    except OSError:
        success = False
    return CheckResult(
        f"tcp.{port}", target.device_id, success, evidence=("TCP",), metrics={"port": int(port)}
    )


def service(target, timeout=0.8, *, name="", port=None, workers=4) -> CheckResult:
    """Comprueba un servicio concreto o hace un sondeo acotado de servicios comunes."""
    if port is not None:
        result = tcp_port(target, int(port), timeout)
        return CheckResult(
            "service",
            target.device_id,
            result.success,
            result.timestamp,
            result.latencyMs,
            result.evidence,
            {**result.metrics, "service": name or f"tcp/{port}"},
            result.error,
        )
    from app.monitor.operations import scan_target

    value = scan_target(target, "services", timeout, min(max(1, int(workers)), 4))
    ports = value.get("open_ports", [])
    success = bool(value.get("reachable", False))
    if name:
        success = any(str(item.get("service", "")).casefold() == name.casefold() for item in ports)
    return CheckResult(
        "service",
        target.device_id,
        success,
        evidence=("TCP-SCAN",),
        metrics={"service": name, "openPorts": [item.get("port") for item in ports]},
    )


def deep(target, timeout=0.8, *, workers=4) -> CheckResult:
    from app.monitor.operations import scan_target

    value = scan_target(target, "full", timeout, min(max(1, int(workers)), 4))
    return CheckResult(
        "deep",
        target.device_id,
        bool(value.get("reachable", False)),
        latencyMs=value.get("latency_ms"),
        evidence=("DEEP-SCAN",),
        metrics={"openPorts": [item.get("port") for item in value.get("open_ports", [])]},
    )
