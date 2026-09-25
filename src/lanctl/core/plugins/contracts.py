from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import datetime
from typing import Any, TypeVar


@dataclass(frozen=True, slots=True)
class EventMetadata:
    event_id: str
    event_version: int
    source: str
    timestamp: datetime
    correlation_id: str


@dataclass(frozen=True, slots=True)
class EventContract:
    metadata: EventMetadata

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class FunctionResult:
    success: bool
    code: str = "OK"
    message: str = ""
    data: Any = None

    def to_dict(self) -> dict[str, Any]:
        return _serialize(asdict(self))


@dataclass(frozen=True, slots=True)
class LifecycleEvent(EventContract):
    version: str
    mode: str


@dataclass(frozen=True, slots=True)
class ProjectFileEvent(EventContract):
    path: str
    project_id: str | None = None


@dataclass(frozen=True, slots=True)
class NetworkScanEvent(EventContract):
    scan_id: str
    target_range: str | None
    running: bool
    active: bool
    devices: int = 0


@dataclass(frozen=True, slots=True)
class DeviceRemoteEvent(EventContract):
    selector: str
    protocol: str
    connected: bool


@dataclass(frozen=True, slots=True)
class VaultOperationEvent(EventContract):
    """Never carries paths, usernames, passwords, keys or decrypted entries."""

    operation: str
    count: int


@dataclass(frozen=True, slots=True)
class NetworkLabEvent(EventContract):
    scenario_id: str
    seed: int | None = None
    path: str | None = None
    device_id: str | None = None
    action: str | None = None
    clock: float | None = None


T = TypeVar("T")


def construct_contract(contract: type[T], values: Mapping[str, Any]) -> T:
    """Construye únicamente campos declarados; los faltantes los valida dataclasses."""
    if not is_dataclass(contract):
        raise TypeError("un contrato debe ser una dataclass")
    allowed = {item.name for item in fields(contract)}
    unknown = sorted(set(values) - allowed)
    if unknown:
        raise ValueError(f"campos no declarados: {', '.join(unknown)}")
    return contract(**dict(values))


def _serialize(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value
