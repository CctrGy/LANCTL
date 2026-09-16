from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path

from lanctl.apps.ip.domain.models import Device
from lanctl.apps.ip.domain.models.device import reserved_device_role

RETENTION_MODES = ("permanent", "session", "forget")
RETENTION_TARGETS = ("unconfirmed", "all")
RETENTION_SCOPES = ("all", "dhcp")

_SESSION_DEVICES: dict[str, list[Device]] = {}


@dataclass(frozen=True)
class RetentionResult:
    persistent: list[Device]
    visible: list[Device]
    removed: tuple[Device, ...] = ()
    session_only: tuple[Device, ...] = ()


def normalize_retention_mode(value: object) -> str:
    normalized = str(value or "permanent").strip().casefold()
    aliases = {"keep": "permanent", "memory": "session", "delete": "forget"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in RETENTION_MODES:
        raise ValueError(f"retención no válida: {value}. Opciones: {', '.join(RETENTION_MODES)}")
    return normalized


def normalize_retention_target(value: object) -> str:
    normalized = str(value or "unconfirmed").strip().casefold()
    aliases = {"unknown": "unconfirmed", "cnf=x": "unconfirmed", "disconnected": "all"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in RETENTION_TARGETS:
        raise ValueError(f"objetivo no válido: {value}. Opciones: {', '.join(RETENTION_TARGETS)}")
    return normalized


def normalize_retention_scope(value: object) -> str:
    normalized = str(value or "all").strip().casefold()
    aliases = {"any": "all", "dynamic": "dhcp"}
    normalized = aliases.get(normalized, normalized)
    if normalized not in RETENTION_SCOPES:
        raise ValueError(f"alcance no válido: {value}. Opciones: {', '.join(RETENTION_SCOPES)}")
    return normalized


def _database_key(path: str | Path) -> str:
    return str(Path(path).resolve()).casefold()


def session_devices(path: str | Path) -> list[Device]:
    return [device.copy() for device in _SESSION_DEVICES.get(_database_key(path), ())]


def clear_session_devices(path: str | Path | None = None) -> None:
    if path is None:
        _SESSION_DEVICES.clear()
    else:
        _SESSION_DEVICES.pop(_database_key(path), None)


def with_session_devices(path: str | Path, devices: list[Device]) -> list[Device]:
    """Combina el inventario persistente y el temporal sin duplicar identidades."""

    combined = [_copy_device(device) for device in devices]
    cached = session_devices(path)
    if not cached:
        return combined
    identities = {_identity(device) for device in combined}
    for device in cached:
        if _identity(device) not in identities:
            combined.append(device)
    return _sorted(combined)


def apply_retention(
    path: str | Path,
    devices: list[Device],
    activity: list[bool],
    *,
    mode: object = "permanent",
    target: object = "unconfirmed",
    scope: object = "all",
    dhcp_range: str | None = None,
) -> RetentionResult:
    """Separa el inventario persistente del temporal tras un descubrimiento.

    Solo se evalúan dispositivos ausentes en el escaneo actual. Los elementos
    estructurales reservados nunca se eliminan ni pasan a memoria de sesión.
    """

    normalized_mode = normalize_retention_mode(mode)
    normalized_target = normalize_retention_target(target)
    normalized_scope = normalize_retention_scope(scope)
    if len(devices) != len(activity):
        raise ValueError("devices y activity deben tener la misma longitud")
    key = _database_key(path)
    if normalized_mode == "permanent":
        _SESSION_DEVICES.pop(key, None)
        copied = _sorted([device.copy() for device in devices])
        return RetentionResult(copied, [device.copy() for device in copied])

    persistent: list[Device] = []
    affected: list[Device] = []
    for device, active in zip(devices, activity):
        if active or not _matches(device, normalized_target, normalized_scope, dhcp_range):
            persistent.append(device.copy())
        else:
            affected.append(device.copy())

    if normalized_mode == "session":
        _SESSION_DEVICES[key] = [device.copy() for device in affected]
        visible = _sorted([*persistent, *affected])
        return RetentionResult(
            _sorted(persistent),
            visible,
            session_only=tuple(device.copy() for device in affected),
        )

    _SESSION_DEVICES.pop(key, None)
    persistent = _sorted(persistent)
    return RetentionResult(
        persistent,
        [device.copy() for device in persistent],
        removed=tuple(device.copy() for device in affected),
    )


def _matches(device: Device, target: str, scope: str, dhcp_range: str | None) -> bool:
    if reserved_device_role(device.alias, device.default_alias):
        return False
    if target == "unconfirmed" and device.cnf != "X":
        return False
    return scope != "dhcp" or _ip_in_range(device.ip, dhcp_range)


def _ip_in_range(value: str, configured_range: str | None) -> bool:
    if not configured_range:
        return False
    try:
        raw_start, raw_end = configured_range.split("-", 1)
        address = ipaddress.IPv4Address(value)
        start = ipaddress.IPv4Address(raw_start.strip())
        end = ipaddress.IPv4Address(raw_end.strip())
    except (ValueError, ipaddress.AddressValueError):
        return False
    return start <= address <= end


def _identity(device: Device) -> str:
    return (
        str(getattr(device, "device_id", ""))
        or str(getattr(device, "mac", "")).upper()
        or str(getattr(device, "ip", ""))
    )


def _copy_device(device: Device) -> Device:
    copier = getattr(device, "copy", None)
    return copier() if callable(copier) else device


def _sorted(devices: list[Device]) -> list[Device]:
    def key(device: Device) -> tuple[int, int, str]:
        try:
            return 0, int(ipaddress.IPv4Address(device.ip)), ""
        except ipaddress.AddressValueError:
            return 1, 0, _identity(device)

    return sorted(devices, key=key)
