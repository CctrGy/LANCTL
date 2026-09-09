from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from lanctl.apps.ip.domain.models import Device


@dataclass(frozen=True, slots=True)
class DiscoveryResult:
    """Resultado común producido por descubrimiento real o simulado."""

    devices: tuple[Device, ...]
    source: str
    provider: str
    scenario_id: str = ""
    seed: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def simulated(self) -> bool:
        return self.source == "simulated"


@runtime_checkable
class DiscoveryProvider(Protocol):
    provider_id: str

    def discover(self, **options: Any) -> DiscoveryResult: ...


def require_real_target(device: Device) -> None:
    """Impide que transportes reales operen sobre identidades de laboratorio."""

    if "SIMULATED" in device.discovery_methods or device.protocol_options.get("simulation"):
        raise PermissionError("acción real bloqueada: el elemento procede de una simulación LANLAB")
