from __future__ import annotations

import json
from collections.abc import Mapping

from app.core.paths import application_path
from app.models import Device, normalize_mac

RECURRENT_ELEMENTS_RESOURCE = "data/lc/recurrent-elements.json"


class RecurrentElementDatabase:
    """Catálogo de identidades que acompaña a LANCTL entre distintas LAN."""

    def __init__(self) -> None:
        self._devices: list[Device] | None = None
        self._by_mac: dict[str, Device] | None = None

    def load(self) -> list[Device]:
        if self._devices is not None:
            return [device.copy() for device in self._devices]
        path = application_path(RECURRENT_ELEMENTS_RESOURCE)
        if not path.exists():
            return []
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                "la base de elementos recurrentes no contiene JSON válido "
                f"(línea {error.lineno}, columna {error.colno}): {path}"
            ) from error
        except UnicodeDecodeError as error:
            raise ValueError(
                f"la base de elementos recurrentes no está codificada como UTF-8: {path}"
            ) from error
        if not isinstance(value, list):
            # Es contenido externo inválido, no un uso incorrecto de la API.
            raise ValueError(f"la base de elementos recurrentes debe contener una lista: {path}")

        devices: list[Device] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, dict) or not item.get("MAC"):
                raise ValueError(f"cada elemento recurrente debe incluir una MAC: {path}")
            # El inventario LAN migra un NAME antiguo a defaultName para no
            # pisar ediciones. En este catálogo NAME ya es una identidad
            # deliberada, por lo que se conservan ambos valores.
            device = Device.from_dict(
                {
                    "IP": "-",
                    **item,
                    "defaultName": item.get("defaultName", item.get("NAME", "")),
                }
            )
            device.mac = normalize_mac(device.mac)
            if device.mac in seen:
                raise ValueError(f"MAC repetida en la base de elementos recurrentes: {device.mac}")
            seen.add(device.mac)
            devices.append(device)
        self._devices = devices
        # El catálogo se consulta por cada resultado de un escaneo. Mantener
        # este índice evita recorrer toda la lista para cada dirección MAC.
        self._by_mac = {device.mac: device for device in devices}
        return [device.copy() for device in devices]

    def find_by_mac(self, mac: str) -> Device | None:
        if self._by_mac is None:
            self.load()
        device = (self._by_mac or {}).get(mac)
        return device.copy() if device is not None else None

    def enrich(self, record: Mapping[str, object] | Device) -> dict[str, object]:
        """Añade identidad recurrente sin introducir IPs de una LAN anterior."""
        result = dict(record)
        raw_mac = str(result.get("MAC", ""))
        if not raw_mac:
            return result
        try:
            mac = normalize_mac(raw_mac)
        except ValueError:
            return result
        recurrent = self.find_by_mac(mac)
        if recurrent is None:
            return result

        name = recurrent.name or recurrent.default_name
        defaults = {
            "cnf": recurrent.cnf,
            "ALIAS": recurrent.alias,
            "defaultAlias": recurrent.alias,
            "NAME": name,
            "defaultName": name,
            "GROUP": list(recurrent.groups),
            "description": recurrent.description,
            "manufacturer": recurrent.manufacturer,
        }
        for field, value in defaults.items():
            if not result.get(field) and value not in ("", [], "-"):
                result[field] = value
        return result
