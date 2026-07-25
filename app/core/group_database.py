from __future__ import annotations

import json
from pathlib import Path

from app.core.database import DeviceDatabase
from app.core.paths import application_path
from app.models import Device, Group


class GroupDatabase:
    def __init__(self, path: str, devices: DeviceDatabase):
        self.path = application_path(path)
        self.devices = devices

    def load(self) -> list[Group]:
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
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                [group.to_dict() for group in groups],
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

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

    def ensure_basic(self, devices: list[Device]) -> list[Group]:
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

        self.devices.save_devices(devices)
        self._write(groups)
        return groups

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

    def delete(self, name: str) -> None:
        normalized = name.upper()
        groups = self.load()
        target = self._find(groups, normalized)
        self._require_editable(target)
        groups.remove(target)
        devices = self.devices.load()
        for device in devices:
            device.groups = [group for group in device.groups if group != normalized]
        self.devices.save_devices(devices)
        self._write(groups)

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
        for device in devices:
            device.groups = [
                replacement if group == normalized else group
                for group in device.groups
            ]
        self.devices.save_devices(devices)
        self._write(groups)
        return target

    def set_description(self, name: str, description: str) -> Group:
        if len(description) > 32:
            raise ValueError("la descripción no puede superar 32 caracteres")
        groups = self.load()
        target = self._find(groups, name)
        self._require_editable(target)
        target.description = description or "-"
        self._write(groups)
        return target

    def add(self, group_name: str, selector: str) -> tuple[Group, Device]:
        groups = self.load()
        group = self._find(groups, group_name)
        self._require_editable(group)
        devices = self.devices.load()
        device = self.devices.resolve(selector)
        if not device.mac:
            raise ValueError("el elemento debe tener MAC para pertenecer a un grupo")
        target = next(item for item in devices if item.mac == device.mac)
        if target.mac not in group.members:
            group.members.append(target.mac)
        if group.name not in target.groups:
            target.groups.append(group.name)
        self.devices.save_devices(devices)
        self._write(groups)
        return group, target

    def remove(self, group_name: str, selector: str) -> tuple[Group, Device]:
        groups = self.load()
        group = self._find(groups, group_name)
        self._require_editable(group)
        devices = self.devices.load()
        device = self.devices.resolve(selector)
        if not device.mac:
            raise ValueError("el elemento debe tener MAC para pertenecer a un grupo")
        target = next(item for item in devices if item.mac == device.mac)
        group.members = [mac for mac in group.members if mac != target.mac]
        target.groups = [name for name in target.groups if name != group.name]
        self.devices.save_devices(devices)
        self._write(groups)
        return group, target
