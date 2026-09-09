from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from lanctl.apps.ip.domain.discovery import DiscoveryResult
from lanctl.apps.ip.domain.models import Device
from lanctl.apps.ip.lab.scenario import LabRepository


class LabDiscoveryProvider:
    provider_id = "lanctl.lab.network-emulator"

    def __init__(self, repository: LabRepository | None = None) -> None:
        self.repository = repository or LabRepository()

    def discover(self, **_options: Any) -> DiscoveryResult:
        scenario = self.repository.active()
        if not scenario:
            raise ValueError("no hay ningún escenario LANLAB activo")
        now = datetime.now(timezone.utc).isoformat()
        devices = []
        for row in scenario["devices"]:
            if not row.get("active"):
                continue
            devices.append(
                Device(
                    ip=row["ip"],
                    mac=row["mac"],
                    cnf=row.get("cnf", "X"),
                    alias=row.get("alias", ""),
                    name=row.get("name", ""),
                    default_name=row.get("hostname", ""),
                    groups=[row.get("group", "LAB")],
                    description=row.get("description", "-"),
                    manufacturer=row.get("manufacturer", "LANLAB"),
                    protocols=[
                        item["service"] for item in row.get("ports", []) if item.get("service")
                    ],
                    discovery_methods=["SIMULATED"],
                    last_discovery="SIMULATED",
                    last_seen=now,
                    protocol_options={
                        "simulation": {
                            "scenarioId": scenario["id"],
                            "provider": self.provider_id,
                            "seed": scenario.get("seed"),
                            "latencyMs": row.get("latencyMs"),
                        }
                    },
                )
            )
        return DiscoveryResult(
            tuple(devices),
            "simulated",
            self.provider_id,
            scenario["id"],
            scenario.get("seed"),
            {"profile": scenario["profile"], "clock": scenario.get("clock", 0)},
        )

    def scan(self, **options: Any) -> list[Device]:
        return list(self.discover(**options).devices)

    @staticmethod
    def is_confirmed(device: Device) -> bool:
        return "SIMULATED" in device.discovery_methods

    @staticmethod
    def discovery_for(device: Device) -> str:
        return "+".join(device.discovery_methods) or "SIMULATED"

    @staticmethod
    def response_time_for(device: Device) -> float | None:
        return device.protocol_options.get("simulation", {}).get("latencyMs")
