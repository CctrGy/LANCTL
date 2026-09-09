from __future__ import annotations

from typing import Any

from lanctl.apps.ip.domain.discovery import DiscoveryResult


class RealDiscoveryProvider:
    provider_id = "lanctl.discovery.real"

    def __init__(self, scanner) -> None:
        self.scanner = scanner

    def discover(self, **options: Any) -> DiscoveryResult:
        devices = tuple(self.scanner.scan(**options))
        return DiscoveryResult(devices, "real", self.provider_id)
