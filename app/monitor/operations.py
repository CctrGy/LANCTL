from __future__ import annotations

import statistics
import time
from dataclasses import asdict

from app.monitor.checks import availability
from app.services.element_scanner import ElementScanner, parse_ports
from app.services.lan_scanner import active_arp_mac


class BoundedRunner:
    def __init__(self, clock=time.monotonic, sleeper=time.sleep):
        self.clock = clock
        self.sleeper = sleeper

    def run(self, operation, *, interval, duration, cancel=None, max_runs=10000):
        if not 1 <= interval <= 3600:
            raise ValueError("interval debe estar entre 1s y 1h")
        if not 0 <= duration <= 86400:
            raise ValueError("duration debe estar entre 0 y 24h")
        started = self.clock()
        rows = []
        while len(rows) < max_runs and not (cancel and cancel()):
            rows.append(operation())
            if duration <= 0 or self.clock() - started + interval > duration:
                break
            self.sleeper(interval)
        return rows


def ping_targets(
    targets, metrics, session_id, *, interval, duration, timeout, runner=None, cancel=None
):
    runner = runner or BoundedRunner()
    rows = []

    def cycle():
        current = []
        for target in targets:
            result = availability(target, timeout)
            metrics.write(result, session_id)
            current.append(result)
            rows.append(result)
        return current

    runner.run(cycle, interval=interval, duration=duration, cancel=cancel)
    latencies = [x.latencyMs for x in rows if x.latencyMs is not None]
    total = len(rows)
    failed = sum(not x.success for x in rows)
    return {
        "status": "completed",
        "samples": total,
        "received": total - failed,
        "lossPercent": failed * 100 / total if total else 0,
        "latencyMs": {
            "min": min(latencies) if latencies else None,
            "avg": statistics.fmean(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
        },
        "results": [asdict(x) for x in rows],
    }


def scan_target(target, scan_type, timeout, workers):
    if scan_type == "presence":
        return asdict(availability(target, timeout))
    if scan_type == "identity":
        return identify_target(target, timeout)
    ports = parse_ports("common")
    scanner = ElementScanner(timeout, min(max(1, workers), 64))
    result = scanner.scan(
        target.ip,
        ports,
        banners=scan_type in {"services", "full"},
        identify=scan_type in {"services", "full"},
        manufacturer=target.manufacturer,
    )
    value = asdict(result)
    value["type"] = scan_type
    return value


def identify_target(target, timeout=0.8):
    observed = active_arp_mac(target.ip, timeout) if target.ip and target.ip != "-" else ""
    evidence = []
    if observed:
        evidence.append("ARP")
    if target.mac and observed:
        confidence = "confirmed" if target.mac.casefold() == observed.casefold() else "conflict"
    elif target.mac:
        confidence = "medium"
        evidence.append("registered-mac")
    else:
        confidence = "unknown"
    return {
        "deviceId": target.device_id,
        "label": target.alias or target.name or target.ip,
        "ip": target.ip,
        "registeredMac": target.mac,
        "observedMac": observed,
        "confidence": confidence,
        "evidence": evidence,
        "identityMatch": None
        if not target.mac or not observed
        else target.mac.casefold() == observed.casefold(),
    }
