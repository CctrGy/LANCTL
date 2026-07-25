from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScanProfile:
    name: str
    discovery: str
    timeout_factor: float
    workers_factor: float
    attempts: int
    resolve_names: bool
    extra_methods: tuple[str, ...]


SCAN_PROFILES = {
    "fast": ScanProfile("fast", "arp", 0.4, 2.0, 1, False, ()),
    "normal": ScanProfile("normal", "hybrid", 1.0, 1.0, 1, False, ("mdns", "ssdp")),
    "accurate": ScanProfile(
        "accurate", "hybrid", 1.75, 0.75, 2, True, ("mdns", "ssdp", "wsd")
    ),
}


def apply_profile(name: str, timeout: float, workers: int) -> tuple[ScanProfile, float, int]:
    try:
        profile = SCAN_PROFILES[name.casefold()]
    except KeyError as error:
        raise ValueError(f"perfil de escaneo no válido: {name}") from error
    return (
        profile,
        max(0.05, timeout * profile.timeout_factor),
        max(1, round(workers * profile.workers_factor)),
    )
