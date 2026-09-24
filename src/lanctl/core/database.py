from __future__ import annotations

import ipaddress
import json
from collections.abc import Iterable, Mapping
from datetime import datetime

from lanctl.apps.ip.domain.models import Device, normalize_cnf, normalize_mac
from lanctl.apps.ip.domain.models.device import is_private_mac, reserved_device_role
from lanctl.core.config import load_config
from lanctl.core.file_transaction import atomic_write_json, transactional_method
from lanctl.core.logger import write_database_log
from lanctl.core.paths import application_path
from lanctl.core.recurrent_elements import RecurrentElementDatabase


class DeviceDatabase:
    """Almacenamiento JSON persistente que identifica dispositivos por MAC."""

    def __init__(self, path: str):
        self.path = application_path(path)

    def load(self) -> list[Device]:
        # Una interrupción entre la escritura de devices y groups deja un
        # journal junto a esta base. Se recupera antes de exponer cualquiera
        # de las dos mitades, incluso si el consumidor abre primero devices.
        from lanctl.core.group_database import recover_device_group_transaction

        recover_device_group_transaction(self.path)
        if not self.path.exists():
            return []
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                "la base de datos no contiene JSON válido "
                f"(línea {error.lineno}, columna {error.colno}): {self.path}"
            ) from error
        except UnicodeDecodeError as error:
            raise ValueError(
                f"la base de datos no está codificada como UTF-8: {self.path}"
            ) from error
        if not isinstance(value, list):
            # Es contenido externo inválido, no un uso incorrecto de la API.
            raise ValueError(f"la base de datos debe contener una lista: {self.path}")

        devices: list[Device] = []
        for item in value:
            if not isinstance(item, dict) or "IP" not in item or "MAC" not in item:
                raise ValueError(
                    f"cada registro de la base de datos debe tener al menos IP y MAC: {self.path}"
                )
            devices.append(Device.from_dict(item))
        return devices

    @transactional_method
    def upsert(self, records: Iterable[Mapping[str, str] | Device]) -> list[Device]:
        # La misma instantánea sirve para fusionar y para generar la auditoría;
        # así evitamos leer y convertir dos veces el JSON en cada escaneo.
        before = self.load()
        devices = self.preview(records, _devices=before)
        self._write(devices, before=before)
        return devices

    def preview(
        self,
        records: Iterable[Mapping[str, str] | Device],
        *,
        _devices: list[Device] | None = None,
    ) -> list[Device]:
        """Fusiona resultados sin modificar todavía la base de datos."""
        devices = list(_devices) if _devices is not None else self.load()
        recurrent_elements = RecurrentElementDatabase()
        # La fusión se ejecuta por cada host descubierto. Estos índices evitan
        # recorrer el inventario completo para localizar cada identidad.
        mac_indexes = {
            device.mac.upper(): index for index, device in enumerate(devices) if device.mac
        }
        ip_indexes = {device.ip: index for index, device in enumerate(devices)}
        reserved_indexes = {
            role: index
            for index, device in enumerate(devices)
            if (role := reserved_device_role(device.alias, device.default_alias))
        }
        for record in records:
            record = recurrent_elements.enrich(record)
            ip = str(record["IP"])
            mac = str(record.get("MAC", "")).upper()
            reserved_role = reserved_device_role(
                str(record.get("ALIAS", "")), str(record.get("defaultAlias", ""))
            )

            # La MAC identifica al dispositivo aunque DHCP le asigne otra IP.
            # Los dos elementos estructurales se identifican antes por su rol:
            # solo puede existir un GATEWAY y un BRODCAST por inventario.
            previous_index = reserved_indexes.get(reserved_role) if reserved_role else None
            if previous_index is None:
                previous_index = mac_indexes.get(mac) if mac else None
            if previous_index is None and mac and is_private_mac(mac):
                candidate_index = ip_indexes.get(ip)
                candidate = devices[candidate_index] if candidate_index is not None else None
                incoming_name = str(record.get("defaultName") or record.get("NAME") or "").strip()
                previous_names = (
                    {candidate.default_name.casefold(), candidate.name.casefold()}
                    if candidate
                    else set()
                )
                explicit_id = str(record.get("deviceId") or "")
                if candidate and (
                    (explicit_id and explicit_id == candidate.device_id)
                    or (incoming_name and incoming_name.casefold() in previous_names)
                ):
                    # Una MAC aleatoria puede rotar manteniendo IP y hostname.
                    # Exigimos evidencia estable para no fusionar dos equipos
                    # distintos que reutilicen una concesión DHCP.
                    previous_index = candidate_index
            # Sin MAC solo puede utilizarse la IP como identidad provisional.
            # Una MAC nueva nunca sustituye otra MAC por compartir la misma IP.
            if previous_index is None and not mac:
                previous_index = ip_indexes.get(ip)
            previous = devices[previous_index] if previous_index is not None else None

            incoming = Device.from_dict(
                {
                    "IP": ip,
                    "cnf": normalize_cnf(record.get("cnf", False)),
                    "ALIAS": str(record.get("ALIAS", "")),
                    "defaultAlias": str(record.get("defaultAlias", record.get("ALIAS", ""))),
                    "MAC": mac,
                    "NAME": str(record.get("NAME", "")),
                    "GROUP": list(record.get("GROUP", [])),
                    "description": str(record.get("description", "-")),
                    "manufacturer": str(record.get("manufacturer", "")),
                    "defaultName": str(record.get("defaultName", "")),
                    "nameDeleted": bool(record.get("nameDeleted", False)),
                    "aliasDeleted": bool(record.get("aliasDeleted", False)),
                    "deviceId": str(record.get("deviceId", "")),
                    "idf": str(record.get("idf", "")),
                    "protocols": list(record.get("protocols", [])),
                    "credentials": dict(record.get("credentials", {})),
                    "protocolOptions": dict(record.get("protocolOptions", {})),
                    "discoveryMethods": list(record.get("discoveryMethods", [])),
                    "lastDiscovery": str(record.get("lastDiscovery", "")),
                    "lastSeen": str(record.get("lastSeen", "")),
                    "iconId": str(record.get("iconId", "")),
                }
            )
            if previous:
                incoming["cnf"] = "O" if reserved_role else previous["cnf"]
                incoming["GROUP"] = list(dict.fromkeys([*previous["GROUP"], *incoming["GROUP"]]))
                if previous["description"] != "-":
                    incoming["description"] = previous["description"]
                # Un escaneo incompleto no elimina datos ya vinculados.
                for field in ("MAC", "manufacturer", "defaultName", "defaultAlias"):
                    if not incoming[field]:
                        incoming[field] = previous[field]
                # NAME se asigna una sola vez. Si ya existe, tanto si es
                # automático como si lo editó el usuario, ningún escaneo vuelve
                # a escribirlo.
                incoming["nameDeleted"] = previous["nameDeleted"]
                incoming["NAME"] = (
                    "" if previous["nameDeleted"] else previous["NAME"] or incoming["defaultName"]
                )
                incoming["aliasDeleted"] = previous["aliasDeleted"]
                incoming.device_id = previous.device_id
                incoming.idf = previous.idf
                incoming.protocols = list(previous.protocols)
                incoming.credentials = dict(previous.credentials)
                incoming.protocol_options = {
                    protocol: dict(options)
                    for protocol, options in previous.protocol_options.items()
                }
                incoming.discovery_methods = list(
                    dict.fromkeys([*previous.discovery_methods, *incoming.discovery_methods])
                )
                if not incoming.last_discovery:
                    incoming.last_discovery = previous.last_discovery
                if not incoming.last_seen:
                    incoming.last_seen = previous.last_seen
                incoming.icon_id = previous.icon_id
                incoming.previous_ips = list(previous.previous_ips)
                if previous.ip and previous.ip != incoming.ip:
                    incoming.previous_ips = list(
                        dict.fromkeys([*incoming.previous_ips, previous.ip])
                    )
                if previous["aliasDeleted"]:
                    incoming["ALIAS"] = ""
                elif previous["ALIAS"] and previous["ALIAS"] != previous["defaultAlias"]:
                    incoming["ALIAS"] = previous["ALIAS"]
                incoming.apply_reserved_defaults()
            elif not incoming["NAME"]:
                # Primer descubrimiento de la MAC: el nombre detectado sirve
                # como etiqueta inicial y luego queda protegido.
                incoming["NAME"] = incoming["defaultName"]
            if previous:
                if previous.mac and previous.mac.upper() != incoming.mac.upper():
                    mac_indexes.pop(previous.mac.upper(), None)
                devices[previous_index] = incoming
            else:
                previous_index = len(devices)
                devices.append(incoming)

            # Un host puede adquirir MAC o cambiar de IP durante el proceso de
            # identificación; el índice debe reflejar el registro fusionado.
            if incoming.mac:
                mac_indexes[incoming.mac.upper()] = previous_index
            ip_indexes[incoming.ip] = previous_index
            if role := incoming.apply_reserved_defaults():
                reserved_indexes[role] = previous_index

        def address_key(device: Device) -> tuple[int, int]:
            try:
                return 0, int(ipaddress.IPv4Address(device.ip))
            except ipaddress.AddressValueError:
                return 1, 0

        return sorted(devices, key=address_key)

    @transactional_method
    def record_detection(
        self, selector: str, methods: Iterable[str], seen_at: str | None = None
    ) -> Device:
        """Añade evidencia de descubrimiento sin alterar identidad ni etiquetas."""
        devices, device = self._find(selector)
        normalized = list(
            dict.fromkeys(str(method).strip().upper() for method in methods if str(method).strip())
        )
        if not normalized:
            return device.copy()
        device.discovery_methods = list(dict.fromkeys([*device.discovery_methods, *normalized]))
        device.last_discovery = "+".join(normalized)
        device.last_seen = seen_at or datetime.now().astimezone().isoformat(timespec="seconds")
        self._write(devices)
        return device.copy()

    @transactional_method
    def _write(self, devices: list[Device], *, before: list[Device] | None = None) -> None:
        if before is None:
            before = self.load() if self.path.exists() else []
        atomic_write_json(self.path, [device.to_dict() for device in devices])
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
                field
                for field in sorted(current[identity])
                if previous[identity].get(field) != current[identity].get(field)
            ]
            if changed:
                details = []
                for field in changed:
                    if field.casefold() == "credentials":
                        old_value = new_value = "[OCULTO]"
                    else:
                        old_value = json.dumps(
                            previous[identity].get(field),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                        new_value = json.dumps(
                            current[identity].get(field),
                            ensure_ascii=False,
                            separators=(",", ":"),
                        )
                    details.append(f"{field}:{old_value}=>{new_value}")
                entries.append(f"CAMBIO {identity} {'; '.join(details)}")

        for entry in entries:
            write_database_log(entry)
        try:
            from lanctl.core.history import DeviceSnapshot, HistoryEvent, HistoryService

            service = HistoryService()

            def snapshot(value):
                return DeviceSnapshot(
                    str(value.get("deviceId", "")),
                    str(value.get("MAC", "")),
                    str(value.get("IP", "")),
                    str(value.get("ALIAS") or value.get("NAME") or value.get("IP") or ""),
                )

            for identity in sorted(current.keys() - previous.keys()):
                service.write(
                    HistoryEvent(
                        "device.created",
                        "lanctl.database",
                        "local",
                        "success",
                        "Dispositivo añadido al inventario",
                        device=snapshot(current[identity]),
                        operationId="database.device.update",
                    )
                )
            for identity in sorted(previous.keys() - current.keys()):
                service.write(
                    HistoryEvent(
                        "device.deleted",
                        "lanctl.database",
                        "local",
                        "success",
                        "Dispositivo eliminado del inventario",
                        device=snapshot(previous[identity]),
                        operationId="database.device.update",
                    )
                )
            type_by_field = {
                "IP": "device.ip.changed",
                "MAC": "device.mac.changed",
                "NAME": "device.name.changed",
                "ALIAS": "device.alias.changed",
                "protocols": "device.protocol.configured",
                "credentials": "device.credential.bound",
            }
            for identity in sorted(previous.keys() & current.keys()):
                changes = []
                for field_name in sorted(current[identity]):
                    if previous[identity].get(field_name) != current[identity].get(field_name):
                        hidden = field_name.casefold() == "credentials"
                        changes.append(
                            {
                                "field": field_name,
                                "before": "[OCULTO]"
                                if hidden
                                else previous[identity].get(field_name),
                                "after": "[OCULTO]"
                                if hidden
                                else current[identity].get(field_name),
                            }
                        )
                if changes:
                    event_type = (
                        type_by_field.get(changes[0]["field"], "device.updated")
                        if len(changes) == 1
                        else "device.updated"
                    )
                    service.write(
                        HistoryEvent(
                            event_type,
                            "lanctl.database",
                            "local",
                            "success",
                            "Inventario del dispositivo actualizado",
                            device=snapshot(current[identity]),
                            changes=tuple(changes),
                            operationId="database.device.update",
                        )
                    )
        except (ValueError, OSError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.Database.History",
                code="DATABASE.HISTORY.WRITE.DEGRADED",
                level=18,
                details={"operation": "database.device.update"},
                print_output=False,
                once_key="database.history.write-degraded",
            )

    @transactional_method
    def save_devices(self, devices: list[Device]) -> None:
        self._write(devices)

    def _find(
        self,
        selector: str,
        *,
        devices: list[Device] | None = None,
    ) -> tuple[list[Device], Device]:
        devices = self.load() if devices is None else devices
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
            or device.device_id.casefold() == selector.casefold()
            or (device.idf and device.idf.casefold() == selector.casefold())
        ]
        if not matches:
            raise ValueError(f"no existe ningún dispositivo para: {selector}")
        if len(matches) > 1:
            raise ValueError(f"el selector coincide con varios dispositivos: {selector}")
        return devices, matches[0]

    def resolve(
        self,
        selector: str,
        *,
        devices: list[Device] | None = None,
    ) -> Device:
        """Alias Call: resuelve MAC, IP o ALIAS al registro completo."""
        _, device = self._find(selector, devices=devices)
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
            or (device.idf and device.idf.casefold() == folded)
        ]
        if not matches:
            raise ValueError(f"no se encontró ningún dispositivo para: {selector}")
        return matches

    @transactional_method
    def set_value(self, selector: str, field: str, mode: str, value: str = "") -> Device:
        devices, device = self._find(selector)
        if field == "NAME":
            default_field, deleted_field = "defaultName", "nameDeleted"
        else:
            default_field, deleted_field = "defaultAlias", "aliasDeleted"
            if device["defaultAlias"] in ("GATEWAY", "BRODCAST"):
                raise ValueError(
                    f"el alias reservado {device['defaultAlias']} no se puede modificar"
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
                        if item is not device and item["ALIAS"].casefold() == value.casefold()
                    ),
                    None,
                )
                if duplicate:
                    raise ValueError(f'el alias "{value}" ya pertenece a {duplicate["MAC"]}')
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

    @transactional_method
    def edit_device(self, selector: str, field: str, value: str) -> Device:
        devices, device = self._edit_device_in_memory(selector, field, value)
        self._write(devices)
        return device

    def _edit_device_in_memory(
        self,
        selector: str,
        field: str,
        value: str,
        *,
        devices: list[Device] | None = None,
    ) -> tuple[list[Device], Device]:
        """Valida y modifica una instantánea sin persistirla.

        La operación compuesta de ``element`` utiliza esta variante para poder
        validar todos los campos antes de realizar una única escritura.
        """

        devices, device = self._find(selector, devices=devices)
        if field in ("name", "alias"):
            storage_field = "NAME" if field == "name" else "ALIAS"
            if storage_field == "NAME":
                deleted_field = "nameDeleted"
            else:
                deleted_field = "aliasDeleted"
                if device["defaultAlias"] in ("GATEWAY", "BRODCAST"):
                    raise ValueError(
                        f"el alias reservado {device['defaultAlias']} no se puede modificar"
                    )
                if value:
                    duplicate = next(
                        (
                            item
                            for item in devices
                            if item is not device and item["ALIAS"].casefold() == value.casefold()
                        ),
                        None,
                    )
                    if duplicate:
                        raise ValueError(f'el alias "{value}" ya pertenece a {duplicate["MAC"]}')
            device[storage_field] = value
            device[deleted_field] = False
            device.cnf = "O"
        elif field == "description":
            if len(value) > 42:
                raise ValueError("la descripción no puede superar 42 caracteres")
            device.description = value or "-"
        elif field == "ip":
            try:
                normalized_ip = str(ipaddress.IPv4Address(value.strip()))
            except ipaddress.AddressValueError as error:
                raise ValueError(f"dirección IPv4 no válida: {value}") from error
            duplicate = next(
                (item for item in devices if item is not device and item.ip == normalized_ip),
                None,
            )
            if duplicate:
                owner = duplicate.alias or duplicate.name or duplicate.mac or duplicate.device_id
                raise ValueError(f"la IP {normalized_ip} ya pertenece a {owner}")
            device.ip = normalized_ip
        elif field == "cnf":
            device.cnf = normalize_cnf(value)
        elif field == "idf":
            from lanctl.apps.wire.idf import IDF

            normalized_idf = str(IDF.parse(value)) if value.strip() else ""
            duplicate = next(
                (
                    item
                    for item in devices
                    if item is not device and item.idf.casefold() == normalized_idf.casefold()
                ),
                None,
            )
            if duplicate:
                owner = duplicate.alias or duplicate.name or duplicate.mac or duplicate.device_id
                raise ValueError(f"el IDF {normalized_idf} ya pertenece a {owner}")
            device.idf = normalized_idf
        elif field == "icon":
            normalized = value.strip().casefold()
            if normalized and not normalized.startswith("device."):
                raise ValueError("identificador de icono de dispositivo no válido")
            device.icon_id = normalized
        else:
            raise ValueError(f"campo de elemento no editable: {field}")
        return devices, device

    def _set_protocol_in_memory(
        self,
        selector: str,
        protocol: str,
        enabled: bool,
        *,
        devices: list[Device] | None = None,
    ) -> tuple[list[Device], Device]:
        from lanctl.apps.ip.domain.models import normalize_protocol

        devices, device = self._find(selector, devices=devices)
        normalized = normalize_protocol(protocol)
        if enabled and normalized not in device.protocols:
            device.protocols.append(normalized)
        elif not enabled:
            if normalized in device.credentials:
                raise ValueError(
                    f"el protocolo {normalized} tiene una credencial asociada; elimínala primero"
                )
            device.protocols = [item for item in device.protocols if item != normalized]
        return devices, device

    @transactional_method
    def add_device(
        self,
        mac: str,
        name: str = "",
        alias: str = "",
        description: str = "-",
        ip: str = "-",
        idf: str = "",
    ) -> Device:
        normalized_mac = normalize_mac(mac)
        if ip == "-":
            normalized_ip = "-"
        else:
            try:
                normalized_ip = str(ipaddress.IPv4Address(ip.strip()))
            except ipaddress.AddressValueError as error:
                raise ValueError(f"dirección IPv4 no válida: {ip}") from error
        if len(description) > 42:
            raise ValueError("la descripción no puede superar 42 caracteres")
        if alias.upper() in ("GATEWAY", "BRODCAST"):
            raise ValueError(f"el alias {alias.upper()} está reservado")
        if idf:
            from lanctl.apps.wire.idf import IDF

            idf = str(IDF.parse(idf))

        devices = self.load()
        if any(device.mac == normalized_mac for device in devices):
            raise ValueError(f"ya existe un elemento con la MAC {normalized_mac}")
        if normalized_ip != "-" and any(device.ip == normalized_ip for device in devices):
            raise ValueError(f"la IP {normalized_ip} ya está en uso")
        if alias and any(device.alias.casefold() == alias.casefold() for device in devices):
            raise ValueError(f"el alias {alias} ya está en uso")
        if idf and any(device.idf.casefold() == idf.casefold() for device in devices):
            raise ValueError(f"el IDF {idf} ya está en uso")

        device = Device(
            ip=normalized_ip,
            cnf="O" if name or alias else "X",
            mac=normalized_mac,
            name=name,
            alias=alias,
            description=description or "-",
            idf=idf,
        )
        devices.append(device)
        self._write(devices)
        return device

    @transactional_method
    def bind_credential(self, selector: str, protocol: str, credential_id: str) -> Device:
        from lanctl.apps.ip.domain.models import normalize_protocol

        devices, device = self._find(selector)
        normalized = normalize_protocol(protocol)
        if normalized not in device.protocols:
            device.protocols.append(normalized)
        device.credentials[normalized] = credential_id
        self._write(devices)
        return device.copy()

    @transactional_method
    def unbind_credential(self, selector: str, protocol: str) -> Device:
        from lanctl.apps.ip.domain.models import normalize_protocol

        devices, device = self._find(selector)
        normalized = normalize_protocol(protocol)
        device.credentials.pop(normalized, None)
        self._write(devices)
        return device.copy()

    @transactional_method
    def set_protocol(self, selector: str, protocol: str, enabled: bool) -> Device:
        devices, device = self._set_protocol_in_memory(selector, protocol, enabled)
        self._write(devices)
        return device.copy()

    @transactional_method
    def configure_protocol(
        self, selector: str, protocol: str, options: Mapping[str, object]
    ) -> Device:
        from lanctl.apps.ip.domain.models import normalize_protocol

        devices, device = self._find(selector)
        normalized = normalize_protocol(protocol)
        if normalized not in device.protocols:
            device.protocols.append(normalized)
        device.protocol_options[normalized] = dict(options)
        self._write(devices)
        return device.copy()
