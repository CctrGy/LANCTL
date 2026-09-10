from __future__ import annotations

from collections.abc import Iterable

from lanctl.apps.ip.domain.models import Device


class MemoryDeviceRepository:
    """Inventario de sesión sin rutas ni operaciones de persistencia."""

    def __init__(self) -> None:
        self._devices: list[Device] = []

    def replace(self, devices: Iterable[Device]) -> tuple[Device, ...]:
        self._devices = [device.copy() for device in devices]
        return self.all()

    def all(self) -> tuple[Device, ...]:
        return tuple(device.copy() for device in self._devices)

    def clear(self) -> None:
        self._devices.clear()

    def __enter__(self) -> MemoryDeviceRepository:
        return self

    def __exit__(self, *_exc_info) -> None:
        self.clear()
