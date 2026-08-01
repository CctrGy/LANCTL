from __future__ import annotations

import json
import ipaddress
from pathlib import Path
from typing import Iterable, Mapping
from datetime import datetime

from app.models import Device, normalize_cnf, normalize_mac
from app.core.paths import application_path
from app.core.config import load_config
from app.core.logger import write_database_log
from app.core.recurrent_elements import RecurrentElementDatabase


class DeviceDatabase:
    """Almacenamiento JSON persistente que identifica dispositivos por MAC."""

    def __init__(self, path: str):
        self.path = application_path(path)

    def load(self) -> list[Device]:
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"la base de datos no contiene JSON válido: {self.path}") from error
        if not isinstance(value, list):
            raise ValueError(f"la base de datos debe contener una lista: {self.path}")

        devices: list[Device] = []
        for item in value:
            if not isinstance(item, dict) or "IP" not in item or "MAC" not in item:
                raise ValueError(
                    f"cada registro de la base de datos debe tener al menos IP y MAC: {self.path}"
                )
            devices.append(Device.from_dict(item))
        return devices

    def upsert(
        self, records: Iterable[Mapping[str, str] | Device]
    ) -> list[Device]:
        devices = self.preview(records)
        self._write(devices)
        return devices

    def preview(
        self, records: Iterable[Mapping[str, str] | Device]
    ) -> list[Device]:
        """Fusiona resultados sin modificar todavía la base de datos."""
        devices = self.load()
        recurrent_elements = RecurrentElementDatabase()
        for record in records:
            record = recurrent_elements.enrich(record)
            ip = str(record["IP"])
            mac = str(record.get("MAC", "")).upper()

            # La MAC identifica al dispositivo aunque DHCP le asigne otra IP.
            previous = next(
                (
                    device
                    for device in devices
                    if mac and device["MAC"].upper() == mac
                ),
                None,
            )
            # Sin MAC solo puede utilizarse la IP como identidad provisional.
            # Una MAC nueva nunca sustituye otra MAC por compartir la misma IP.
            if previous is None and not mac:
                previous = next(
                    (device for device in devices if device["IP"] == ip),
                    None,
                )

            incoming = Device.from_dict(
                {
                    "IP": ip,
                    "cnf": normalize_cnf(record.get("cnf", False)),
                    "ALIAS": str(record.get("ALIAS", "")),
                    "defaultAlias": str(
                        record.get("defaultAlias", record.get("ALIAS", ""))
                    ),
                    "MAC": mac,
                    "NAME": str(record.get("NAME", "")),
                    "GROUP": list(record.get("GROUP", [])),
                    "description": str(record.get("description", "-")),
                    "manufacturer": str(record.get("manufacturer", "")),
                    "defaultName": str(record.get("defaultName", "")),
                    "nameDeleted": bool(record.get("nameDeleted", False)),
                    "aliasDeleted": bool(record.get("aliasDeleted", False)),
                    "deviceId": str(record.get("deviceId", "")),
                    "protocols": list(record.get("protocols", [])),
                    "credentials": dict(record.get("credentials", {})),
                    "protocolOptions": dict(record.get("protocolOptions", {})),
                    "discoveryMethods": list(record.get("discoveryMethods", [])),
                    "lastDiscovery": str(record.get("lastDiscovery", "")),
                    "lastSeen": str(record.get("lastSeen", "")),
                }
            )
            if previous:
                incoming["cnf"] = previous["cnf"]
                incoming["GROUP"] = list(
                    dict.fromkeys([*previous["GROUP"], *incoming["GROUP"]])
                )
                if previous["description"] != "-":
                    incoming["description"] = previous["description"]
                # Un escaneo incompleto no elimina datos ya vinculados.
                for field in ("MAC", "manufacturer", "defaultName", "defaultAlias"):
                    if not incoming[field]:
                        incoming[field] = previous[field]
                # NAME se asigna una sola vez. Si ya existe, sea automático o
                # editado por el usuario, ningún escaneo vuelve a escribirlo.
                incoming["nameDeleted"] = previous["nameDeleted"]
                incoming["NAME"] = (
                    "" if previous["nameDeleted"]
                    else previous["NAME"] or incoming["defaultName"]
                )
                incoming["aliasDeleted"] = previous["aliasDeleted"]
                incoming.device_id = previous.device_id
                incoming.protocols = list(previous.protocols)
                incoming.credentials = dict(previous.credentials)
                incoming.protocol_options = {
                    protocol: dict(options)
                    for protocol, options in previous.protocol_options.items()
                }
                incoming.discovery_methods = list(dict.fromkeys([
                    *previous.discovery_methods, *incoming.discovery_methods
                ]))
                if not incoming.last_discovery:
                    incoming.last_discovery = previous.last_discovery
                if not incoming.last_seen:
                    incoming.last_seen = previous.last_seen
                if previous["aliasDeleted"]:
                    incoming["ALIAS"] = ""
                elif previous["ALIAS"] and previous["ALIAS"] != previous["defaultAlias"]:
                    incoming["ALIAS"] = previous["ALIAS"]
            elif not incoming["NAME"]:
                # Primer descubrimiento de la MAC: el nombre detectado sirve
                # como etiqueta inicial y luego queda protegido.
                incoming["NAME"] = incoming["defaultName"]
            if previous:
                devices[devices.index(previous)] = incoming
            else:
                devices.append(incoming)

        def address_key(device: Device) -> tuple[int, int]:
            try:
                return 0, int(ipaddress.IPv4Address(device.ip))
            except ipaddress.AddressValueError:
                return 1, 0

        return sorted(devices, key=address_key)

    def record_detection(
        self, selector: str, methods: Iterable[str], seen_at: str | None = None
    ) -> Device:
        """Añade evidencia de descubrimiento sin alterar identidad ni etiquetas."""
        devices, device = self._find(selector)
        normalized = list(dict.fromkeys(
            str(method).strip().upper() for method in methods if str(method).strip()
        ))
        if not normalized:
            return device.copy()
        device.discovery_methods = list(dict.fromkeys([
            *device.discovery_methods, *normalized
        ]))
        device.last_discovery = "+".join(normalized)
        device.last_seen = seen_at or datetime.now().astimezone().isoformat(timespec="seconds")
        self._write(devices)
        return device.copy()

    def _write(self, devices: list[Device]) -> None:
        before = self.load() if self.path.exists() else []
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                [device.to_dict() for device in devices],
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)
        self._audit_changes(before, devices)

    def _audit_changes(self, before: list[Device], after: list[Device]) -> None:
        """Registra los cambios del inventario principal sin guardar secretos."""
        configured_database = application_path(load_config()["database"]).resolve()
        if self.path.resolve() != configured_database:
            return

        def key(device: Device) -> str:
            return device.device_id or device.mac or device.ip

        previous = {key(device): device.to_dict() for device in before}
        current = {key(device): device.to_dict() for device in after}
        entries: list[str] = []

        for identity in sorted(current.keys() - previous.keys()):
            device = current[identity]
            entries.append(
                f"ALTA {identity} IP={device.get('IP', '-')} "
                f"MAC={device.get('MAC', '-')} ALIAS={device.get('ALIAS', '-') or '-'}"
            )
        for identity in sorted(previous.keys() - current.keys()):
            device = previous[identity]
            entries.append(
                f"BAJA {identity} IP={device.get('IP', '-')} "
                f"MAC={device.get('MAC', '-')} ALIAS={device.get('ALIAS', '-') or '-'}"
            )
        for identity in sorted(previous.keys() & current.keys()):
            changed = [
                field for field in sorted(current[identity])
                if previous[identity].get(field) != current[identity].get(field)
            ]
            if changed:
                details = []
                for field in changed:
                    if field.casefold() == "credentials":
                        old_value = new_value = "[OCULTO]"
                    else:
                        old_value = json.dumps(
                            previous[identity].get(field), ensure_ascii=False,
                            separators=(",", ":"),
                        )
                        new_value = json.dumps(
                            current[identity].get(field), ensure_ascii=False,
                            separators=(",", ":"),
                        )
                    details.append(f"{field}:{old_value}=>{new_value}")
                entries.append(f"CAMBIO {identity} {'; '.join(details)}")

        for entry in entries:
            write_database_log(entry)

    def save_devices(self, devices: list[Device]) -> None:
        self._write(devices)

    def _find(self, selector: str) -> tuple[list[Device], Device]:
        devices = self.load()
        candidate = selector.replace("-", ":").upper()
        try:
            normalized = normalize_mac(candidate)
        except ValueError:
            normalized = candidate
        matches = [
            device
            for device in devices
            if device["MAC"].upper() == normalized
            or device["IP"] == selector
            or device["ALIAS"].casefold() == selector.casefold()
        ]
        if not matches:
            raise ValueError(f"no existe ningún dispositivo para: {selector}")
        if len(matches) > 1:
            raise ValueError(f"el selector coincide con varios dispositivos: {selector}")
        return devices, matches[0]

    def resolve(self, selector: str) -> Device:
        """Alias Call: resuelve MAC, IP o ALIAS al registro completo."""
        _, device = self._find(selector)
        return device.copy()

    def search(self, selector: str) -> list[Device]:
        """Busca coincidencias exactas por alias, nombre, IP o MAC."""
        devices = self.load()
        wanted = selector.strip()
        candidate = wanted.replace("-", ":").upper()
        try:
            normalized_mac = normalize_mac(candidate)
        except ValueError:
            normalized_mac = ""
        folded = wanted.casefold()
        matches = [
            device.copy()
            for device in devices
            if device.ip == wanted
            or (normalized_mac and device.mac.upper() == normalized_mac)
            or (device.alias and device.alias.casefold() == folded)
            or (device.name and device.name.casefold() == folded)
        ]
        if not matches:
            raise ValueError(f"no se encontró ningún dispositivo para: {selector}")
        return matches

    def set_value(
        self, selector: str, field: str, mode: str, value: str = ""
    ) -> Device:
        devices, device = self._find(selector)
        if field == "NAME":
            default_field, deleted_field = "defaultName", "nameDeleted"
        else:
            default_field, deleted_field = "defaultAlias", "aliasDeleted"
            if device["defaultAlias"] in ("GATEWAY", "BRODCAST"):
                raise ValueError(
                    f'el alias reservado {device["defaultAlias"]} no se puede modificar'
                )

        if mode == "default":
            device[field] = device[default_field]
            device[deleted_field] = False
        elif mode == "delete":
            device[field] = ""
            device[deleted_field] = True
        else:
            if field == "ALIAS" and value:
                duplicate = next(
                    (
                        item
                        for item in devices
                        if item is not device
                        and item["ALIAS"].casefold() == value.casefold()
                    ),
                    None,
                )
                if duplicate:
                    raise ValueError(
                        f'el alias "{value}" ya pertenece a {duplicate["MAC"]}'
                    )
            device[field] = value
            device[deleted_field] = False

        # NAME y ALIAS son datos revisados por el usuario: al modificarlos el
        # elemento queda automáticamente confirmado.
        device.cnf = "O"

        self._write(devices)
        return device

    def set_name(self, selector: str, name: str) -> Device:
        return self.set_value(selector, "NAME", "value", name)

    def set_alias(self, selector: str, alias: str) -> Device:
        return self.set_value(selector, "ALIAS", "value", alias)

    def edit_device(self, selector: str, field: str, value: str) -> Device:
        if field in ("name", "alias"):
            return self.set_value(
                selector,
                "NAME" if field == "name" else "ALIAS",
                "value",
                value,
            )

        devices, device = self._find(selector)
        if field == "description":
            if len(value) > 42:
                raise ValueError("la descripción no puede superar 42 caracteres")
            device.description = value or "-"
        elif field == "cnf":
            device.cnf = normalize_cnf(value)
        else:
            raise ValueError(f"campo de elemento no editable: {field}")
        self._write(devices)
        return device

    def add_device(
        self,
        mac: str,
        name: str = "",
        alias: str = "",
        description: str = "-",
    ) -> Device:
        normalized_mac = normalize_mac(mac)
        if len(description) > 42:
            raise ValueError("la descripción no puede superar 42 caracteres")
        if alias.upper() in ("GATEWAY", "BRODCAST"):
            raise ValueError(f"el alias {alias.upper()} está reservado")

        devices = self.load()
        if any(device.mac == normalized_mac for device in devices):
            raise ValueError(f"ya existe un elemento con la MAC {normalized_mac}")
        if alias and any(
            device.alias.casefold() == alias.casefold() for device in devices
        ):
            raise ValueError(f"el alias {alias} ya está en uso")

        device = Device(
            ip="-",
            cnf="O" if name or alias else "X",
            mac=normalized_mac,
            name=name,
            alias=alias,
            description=description or "-",
        )
        devices.append(device)
        self._write(devices)
        return device

    def bind_credential(
        self, selector: str, protocol: str, credential_id: str
    ) -> Device:
        from app.models import normalize_protocol

        devices, device = self._find(selector)
        normalized = normalize_protocol(protocol)
        if normalized not in device.protocols:
            device.protocols.append(normalized)
        device.credentials[normalized] = credential_id
        self._write(devices)
        return device.copy()

    def unbind_credential(self, selector: str, protocol: str) -> Device:
        from app.models import normalize_protocol

        devices, device = self._find(selector)
        normalized = normalize_protocol(protocol)
        device.credentials.pop(normalized, None)
        self._write(devices)
        return device.copy()

    def set_protocol(
        self, selector: str, protocol: str, enabled: bool
    ) -> Device:
        from app.models import normalize_protocol

        devices, device = self._find(selector)
        normalized = normalize_protocol(protocol)
        if enabled and normalized not in device.protocols:
            device.protocols.append(normalized)
        elif not enabled:
            device.protocols = [item for item in device.protocols if item != normalized]
            if normalized in device.credentials:
                raise ValueError(
                    f"el protocolo {normalized} tiene una credencial asociada; "
                    "elimínala primero"
                )
        self._write(devices)
        return device.copy()

    def configure_protocol(
        self, selector: str, protocol: str, options: Mapping[str, object]
    ) -> Device:
        from app.models import normalize_protocol

        devices, device = self._find(selector)
        normalized = normalize_protocol(protocol)
        if normalized not in device.protocols:
            device.protocols.append(normalized)
        device.protocol_options[normalized] = dict(options)
        self._write(devices)
        return device.copy()
