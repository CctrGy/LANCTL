from __future__ import annotations

import base64
import hashlib
import json
from functools import wraps
from pathlib import Path

from lanctl.apps.ip.domain.models import Device, Group
from lanctl.core.database import DeviceDatabase
from lanctl.core.file_transaction import (
    atomic_write_bytes,
    atomic_write_json,
    fsync_directory,
    locked_files,
)
from lanctl.core.paths import application_path


def _transaction(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with locked_files((self.path, self.devices.path)):
            return method(self, *args, **kwargs)

    return wrapper


def _journal_path(devices_path: Path) -> Path:
    return devices_path.with_name(devices_path.name + ".groups.transaction")


def _encoded_snapshot(payload: bytes | None) -> dict:
    if payload is None:
        return {"exists": False, "data": "", "sha256": ""}
    return {
        "exists": True,
        "data": base64.b64encode(payload).decode("ascii"),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _decoded_snapshot(value: dict) -> bytes | None:
    if not value.get("exists"):
        return None
    try:
        payload = base64.b64decode(str(value["data"]), validate=True)
    except (KeyError, ValueError) as error:
        raise ValueError("journal devices/groups no contiene una instantánea válida") from error
    if hashlib.sha256(payload).hexdigest() != value.get("sha256"):
        raise ValueError("checksum del journal devices/groups no coincide")
    return payload


def recover_device_group_transaction(devices_path) -> bool:
    """Revierte un commit incompleto encontrado al abrir cualquiera de las bases."""

    devices_path = application_path(devices_path)
    journal = _journal_path(devices_path)
    if not journal.is_file():
        return False
    try:
        initial = json.loads(journal.read_text(encoding="utf-8"))
        groups_path = application_path(initial["groupsPath"])
    except (KeyError, OSError, json.JSONDecodeError) as error:
        raise ValueError(f"journal devices/groups dañado: {journal}") from error
    with locked_files((devices_path, groups_path)):
        if not journal.is_file():
            return False
        try:
            value = json.loads(journal.read_text(encoding="utf-8"))
            if value.get("schemaVersion") != 1:
                raise ValueError("versión de journal devices/groups no compatible")
            if application_path(value["devicesPath"]).resolve() != devices_path.resolve():
                raise ValueError("el journal no pertenece a esta base de dispositivos")
            if application_path(value["groupsPath"]).resolve() != groups_path.resolve():
                raise ValueError("la ruta de grupos del journal ha cambiado")
            snapshots = value["before"]
            originals = {
                devices_path: _decoded_snapshot(snapshots["devices"]),
                groups_path: _decoded_snapshot(snapshots["groups"]),
            }
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError(f"journal devices/groups dañado: {journal}") from error
        for path, payload in originals.items():
            if payload is None:
                path.unlink(missing_ok=True)
                fsync_directory(path.parent)
            else:
                atomic_write_bytes(path, payload)
        journal.unlink()
        fsync_directory(journal.parent)
        return True


class GroupDatabase:
    def __init__(self, path: str, devices: DeviceDatabase):
        self.path = application_path(path)
        self.devices = devices

    def load(self) -> list[Group]:
        recover_device_group_transaction(self.devices.path)
        if not self.path.exists():
            return [Group("BASIC", "Elementos basicos de la LAN", editable=False)]
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"base de grupos JSON no válida: {self.path}") from error
        if not isinstance(value, list):
            raise ValueError("la base de grupos debe contener una lista")
        return [Group.from_dict(item) for item in value]

    def _write(self, groups: list[Group]) -> None:
        atomic_write_json(self.path, [group.to_dict() for group in groups])

    def _commit_pair(
        self,
        devices: list[Device],
        groups: list[Group],
        *,
        previous_devices: list[Device],
        write_groups: bool = True,
    ) -> None:
        """Confirma los dos JSON o restaura exactamente su estado anterior."""

        originals = {
            self.devices.path: self.devices.path.read_bytes()
            if self.devices.path.exists()
            else None,
            self.path: self.path.read_bytes() if self.path.exists() else None,
        }
        journal = _journal_path(self.devices.path)
        atomic_write_json(
            journal,
            {
                "schemaVersion": 1,
                "devicesPath": str(self.devices.path.resolve()),
                "groupsPath": str(self.path.resolve()),
                "before": {
                    "devices": _encoded_snapshot(originals[self.devices.path]),
                    "groups": _encoded_snapshot(originals[self.path]),
                },
            },
        )
        try:
            atomic_write_json(self.devices.path, [device.to_dict() for device in devices])
            if write_groups:
                self._write(groups)
        except BaseException:
            for path, payload in originals.items():
                if payload is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write_bytes(path, payload)
            journal.unlink(missing_ok=True)
            fsync_directory(journal.parent)
            raise
        journal.unlink()
        fsync_directory(journal.parent)
        self.devices._audit_changes(previous_devices, devices)

    @_transaction
    def edit_device_fields(self, selector: str, edits: list[tuple[str, str]]) -> Device:
        """Aplica una cadena ``element`` como una sola transacción lógica."""

        devices = self.devices.load()
        previous_devices = [device.copy() for device in devices]
        groups = self.load()
        _, target = self.devices._find(selector, devices=devices)
        stable_selector = target.device_id or target.mac or selector

        for field, value in edits:
            if field == "group":
                group = self._find(groups, value)
                self._require_editable(group)
                _, target = self.devices._find(stable_selector, devices=devices)
                if not target.mac:
                    raise ValueError("el elemento debe tener MAC para pertenecer a un grupo")
                if target.mac not in group.members:
                    group.members.append(target.mac)
                if group.name not in target.groups:
                    target.groups.append(group.name)
            elif field == "protocol":
                parts = value.split()
                if not parts:
                    raise ValueError("indica un protocolo")
                protocol = parts[-1]
                enabled = not (
                    len(parts) > 1 and parts[0].casefold() in ("del", "delete", "remove")
                )
                devices, target = self.devices._set_protocol_in_memory(
                    stable_selector, protocol, enabled, devices=devices
                )
            else:
                devices, target = self.devices._edit_device_in_memory(
                    stable_selector, field, value, devices=devices
                )

        self._commit_pair(
            devices,
            groups,
            previous_devices=previous_devices,
            write_groups=any(field == "group" for field, _value in edits),
        )
        return target.copy()

    @staticmethod
    def _find(groups: list[Group], name: str) -> Group:
        normalized = name.upper()
        matches = [group for group in groups if group.name == normalized]
        if not matches:
            raise ValueError(f"no existe el grupo {normalized}")
        return matches[0]

    @staticmethod
    def _require_editable(group: Group) -> None:
        if not group.editable:
            raise ValueError(f"el grupo {group.name} no es editable")

    @_transaction
    def ensure_basic(self, devices: list[Device]) -> list[Group]:
        previous_devices = self.devices.load()
        groups = self.load()
        basic = next((group for group in groups if group.name == "BASIC"), None)
        if basic is None:
            basic = Group("BASIC", "Elementos basicos de la LAN", editable=False)
            groups.insert(0, basic)
        else:
            basic.editable = False

        for device in devices:
            if device.default_alias in ("GATEWAY", "BRODCAST"):
                if "BASIC" not in device.groups:
                    device.groups.append("BASIC")
                if device.mac and device.mac not in basic.members:
                    basic.members.append(device.mac)

        self._commit_pair(devices, groups, previous_devices=previous_devices)
        return groups

    @_transaction
    def create(self, name: str) -> Group:
        normalized = name.upper()
        if not normalized:
            raise ValueError("el nombre del grupo no puede estar vacío")
        groups = self.load()
        if any(group.name == normalized for group in groups):
            raise ValueError(f"el grupo {normalized} ya existe")
        group = Group(normalized)
        groups.append(group)
        self._write(groups)
        return group

    @_transaction
    def delete(self, name: str) -> None:
        normalized = name.upper()
        groups = self.load()
        target = self._find(groups, normalized)
        self._require_editable(target)
        groups.remove(target)
        devices = self.devices.load()
        previous_devices = [device.copy() for device in devices]
        for device in devices:
            device.groups = [group for group in device.groups if group != normalized]
        self._commit_pair(devices, groups, previous_devices=previous_devices)

    @_transaction
    def rename(self, name: str, new_name: str) -> Group:
        normalized = name.upper()
        replacement = new_name.upper()
        groups = self.load()
        target = self._find(groups, normalized)
        self._require_editable(target)
        if any(group.name == replacement for group in groups):
            raise ValueError(f"el grupo {replacement} ya existe")
        target.name = replacement
        devices = self.devices.load()
        previous_devices = [device.copy() for device in devices]
        for device in devices:
            device.groups = [
                replacement if group == normalized else group for group in device.groups
            ]
        self._commit_pair(devices, groups, previous_devices=previous_devices)
        return target

    @_transaction
    def set_description(self, name: str, description: str) -> Group:
        if len(description) > 42:
            raise ValueError("la descripción no puede superar 42 caracteres")
        groups = self.load()
        target = self._find(groups, name)
        self._require_editable(target)
        target.description = description or "-"
        self._write(groups)
        return target

    @_transaction
    def add(self, group_name: str, selector: str) -> tuple[Group, Device]:
        groups = self.load()
        group = self._find(groups, group_name)
        self._require_editable(group)
        devices = self.devices.load()
        previous_devices = [device.copy() for device in devices]
        _, device = self.devices._find(selector, devices=devices)
        if not device.mac:
            raise ValueError("el elemento debe tener MAC para pertenecer a un grupo")
        target = next(item for item in devices if item.mac == device.mac)
        if target.mac not in group.members:
            group.members.append(target.mac)
        if group.name not in target.groups:
            target.groups.append(group.name)
        self._commit_pair(devices, groups, previous_devices=previous_devices)
        return group, target

    @_transaction
    def remove(self, group_name: str, selector: str) -> tuple[Group, Device]:
        groups = self.load()
        group = self._find(groups, group_name)
        self._require_editable(group)
        devices = self.devices.load()
        previous_devices = [device.copy() for device in devices]
        _, device = self.devices._find(selector, devices=devices)
        if not device.mac:
            raise ValueError("el elemento debe tener MAC para pertenecer a un grupo")
        target = next(item for item in devices if item.mac == device.mac)
        group.members = [mac for mac in group.members if mac != target.mac]
        target.groups = [name for name in target.groups if name != group.name]
        self._commit_pair(devices, groups, previous_devices=previous_devices)
        return group, target

    @_transaction
    def delete_device(self, selector: str) -> Device:
        """Elimina un elemento y todas sus referencias de grupo por MAC."""
        devices = self.devices.load()
        _, target = self.devices._find(selector, devices=devices)
        if target.default_alias in ("GATEWAY", "BRODCAST"):
            raise ValueError(f"el elemento reservado {target.default_alias} no se puede eliminar")

        remaining = [device for device in devices if device.mac != target.mac]
        if len(remaining) == len(devices):
            raise ValueError(f"no existe ningún dispositivo para: {selector}")

        groups = self.load()
        for group in groups:
            group.members = [mac for mac in group.members if mac != target.mac]

        self._commit_pair(remaining, groups, previous_devices=devices)
        return target
