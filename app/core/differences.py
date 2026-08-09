from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.models import Device

SCANNED_FIELDS = ("IP", "MAC")
PROTECTED_FIELDS = (
    "cnf",
    "ALIAS",
    "NAME",
    "GROUP",
    "description",
    "manufacturer",
)


@dataclass(frozen=True)
class ScanDifferences:
    rows: list[Device]
    colors: list[dict[str, str]]
    new_devices: int = 0
    ip_changes: int = 0
    mac_conflicts: int = 0
    pending_values: int = 0

    @property
    def changed_devices(self) -> int:
        return self.new_devices + self.ip_changes + self.mac_conflicts

    def summary(self) -> str:
        return (
            f"{self.changed_devices} dispositivos con cambios | "
            f"Nuevos: {self.new_devices} | "
            f"IP no coincidentes: {self.ip_changes} "
            "(se guardan automáticamente) | "
            f"MAC no coincidentes: {self.mac_conflicts}"
        )


def compare_scan(
    records: Iterable[Mapping[str, object]],
    saved: Iterable[Device],
    preview: Iterable[Device],
) -> ScanDifferences:
    """Compara el escaneo pendiente con la base de datos sin modificarla."""
    pending = [dict(record) for record in records]
    saved_devices = list(saved)
    pending_ips = {str(record.get("IP", "")) for record in pending}
    rows = [device for device in preview if device.ip in pending_ips]
    records_by_ip = {str(record.get("IP", "")): record for record in pending}

    colors: list[dict[str, str]] = []
    new_devices = ip_changes = mac_conflicts = pending_values = 0

    for row in rows:
        record = records_by_ip[row.ip]
        incoming_mac = str(record.get("MAC", "")).upper()
        previous_by_mac = next(
            (
                device
                for device in saved_devices
                if incoming_mac and device.mac.upper() == incoming_mac
            ),
            None,
        )
        previous_by_ip = next(
            (device for device in saved_devices if device.ip == row.ip),
            None,
        )
        previous = previous_by_mac or previous_by_ip

        state = {field: "white" for field in PROTECTED_FIELDS}
        if previous is None:
            new_devices += 1
            state.update({field: "red" for field in SCANNED_FIELDS})
        else:
            ip_equal = previous.ip == row.ip
            mac_equal = not incoming_mac or previous.mac.upper() == incoming_mac
            state["IP"] = "blue" if ip_equal else "red"
            state["MAC"] = "blue" if mac_equal else "red"
            if previous_by_mac is not None and not ip_equal:
                ip_changes += 1
            if previous_by_ip is not None and not mac_equal:
                mac_conflicts += 1

        pending_values += sum(state.get(field) == "red" for field in SCANNED_FIELDS)
        colors.append(state)

    return ScanDifferences(
        rows=rows,
        colors=colors,
        new_devices=new_devices,
        ip_changes=ip_changes,
        mac_conflicts=mac_conflicts,
        pending_values=pending_values,
    )
