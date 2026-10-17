"""Structured desktop operations on the same IDF database as CLI/TUI."""

import hashlib
import ipaddress
import json
from copy import deepcopy

from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.topology import (
    build_new_idf_data,
    build_ports,
    compatible_connection,
    groups_for,
)
from lanctl.core.file_transaction import locked_file


def revision(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()


class WireGuiService:
    def __init__(self, path):
        self.database = IDFDatabaseManager(path)

    def snapshot(self):
        from lanctl.apps.rack.organization import snapshot

        with locked_file(self.database.path):
            return {
                "records": [
                    {**r, "revision": revision(r), "filterGroups": sorted(groups_for(r))}
                    for r in self.database.all()
                ],
                "storage": str(self.database.path),
                **snapshot(self.database),
            }

    def _record(self, identifier, expected):
        record = self.database.get(identifier)
        if record is None:
            raise ValueError("El elemento ya no existe; actualiza la lista")
        if revision(record) != expected:
            raise ValueError("El elemento cambió en otra ventana; actualiza antes de editar")
        return record

    @staticmethod
    def _fields(data, values):
        result = deepcopy(data)
        for key in ("name", "alias", "description"):
            if key in values:
                if not isinstance(values[key], str):
                    raise ValueError(f"{key} debe ser texto")
                result[key] = values[key].strip()
        if "rack" in values:
            unit = values.get("unit")
            if unit is not None and (type(unit) is not int or not 1 <= unit <= 100):
                raise ValueError("La unidad debe estar entre 1 y 100")
            result["location"] = {
                **result.get("location", {}),
                "rack": values["rack"],
                "unit": unit,
            }
        if "connectionMode" in values:
            if values["connectionMode"] not in {"wired", "wifi", "mixed"}:
                raise ValueError("Selecciona cable, Wi-Fi o ambas conexiones")
            result["connectionMode"] = values["connectionMode"]
        for key in ("groups", "speeds"):
            if key in values:
                if not isinstance(values[key], list) or not all(
                    isinstance(item, str) for item in values[key]
                ):
                    raise ValueError(f"{key} debe ser una lista de textos")
                result[key] = values[key]
        if "ip" in values:
            if values["ip"]:
                ipaddress.ip_address(values["ip"])
            result["ip"] = values["ip"]
        if "kind" in values:
            if values["kind"] not in {"wire.copper", "wire.fiber", "wire.dac"}:
                raise ValueError("Medio de cable desconocido")
            result["kind"] = values["kind"]
        if "units" in values:
            if type(values["units"]) is not int or not 1 <= values["units"] <= 100:
                raise ValueError("El rack debe tener entre 1 y 100 unidades")
            result["units"] = values["units"]
        return result

    def create(self, values):
        kind = values["kind"]
        if kind == "rack":
            units = int(values.get("units", 42))
            if not 1 <= units <= 100:
                raise ValueError("El rack debe tener entre 1 y 100 unidades")
            data = {"type": "rack", "units": units}
        elif kind in {"panel", "outlet"}:
            data = {
                "type": f"device.{kind}",
                "ports": build_ports(24, "P{n}")
                if kind == "panel"
                else build_ports(2, "WALL,ROOM"),
            }
        else:
            data = build_new_idf_data(kind)
        data = self._fields(
            data,
            {key: value for key, value in values.items() if key not in {"kind", "units"}},
        )
        record = self.database.create(values["prefix"], data=data)
        return {"id": record["id"]}

    def update(self, identifier, expected, values):
        with locked_file(self.database.path):
            record = self._record(identifier, expected)
            data = self._fields(record["data"], values)
            if "portChanges" in values:
                for name, changes in values["portChanges"].items():
                    if name not in data.get("ports", {}):
                        raise ValueError("El puerto ya no existe")
                    if changes.get("kind") not in {
                        "wire.copper",
                        "wire.fiber",
                        "wire.dac",
                        "connection.rj45",
                        "connection.fiber",
                        "connection.dac",
                        "connection.unknown",
                    }:
                        raise ValueError("Medio del puerto desconocido")
                    if type(changes.get("poe")) is not bool:
                        raise ValueError("PoE debe ser activado o desactivado")
                    data["ports"][name].update(kind=changes["kind"], poe=changes["poe"])
            all_records = self.database.all()
            for wire in all_records:
                cable = data if wire["id"] == identifier else wire["data"]
                if cable.get("type") != "wire":
                    continue
                if wire["id"] != identifier and not any(
                    endpoint.get("device") == identifier for endpoint in cable.get("endpoints", [])
                ):
                    continue
                for endpoint in cable.get("endpoints", []):
                    device = (
                        data
                        if endpoint["device"] == identifier
                        else (self.database.get(endpoint["device"]) or {}).get("data", {})
                    )
                    port = device.get("ports", {}).get(endpoint["port"])
                    if port is not None:
                        compatible, reason = compatible_connection(cable, port)
                        if not compatible:
                            raise ValueError(reason)
            if data.get("type") == "rack":
                for other in all_records:
                    location = other["data"].get("location", {})
                    if location.get("rack") == identifier and (
                        location.get("unit") or 0
                    ) > data.get("units", 42):
                        raise ValueError("La altura deja equipos fuera del rack")
            if data.get("location", {}).get("rack"):
                rack = self.database.get(data["location"]["rack"])
                if not rack or rack["data"].get("type") != "rack":
                    raise ValueError("El rack indicado no existe")
                if data["location"].get("unit") and data["location"]["unit"] > int(
                    rack["data"].get("units", 42)
                ):
                    raise ValueError("La unidad excede la altura del rack")
            self.database.update(identifier, data)

    def connect(self, identifier, expected, endpoints):
        if not isinstance(endpoints, list) or len(endpoints) > 2:
            raise ValueError("Un cable admite como máximo dos extremos")
        with locked_file(self.database.path):
            wire = self._record(identifier, expected)
            if wire["data"].get("type") != "wire":
                raise ValueError("Selecciona un cable")
            if wire["data"].get("source") and len(endpoints) > 1:
                raise ValueError("El suministro externo ya ocupa uno de los extremos del cable")
            seen = set()
            normalized = []
            for endpoint in endpoints:
                device = self.database.get(endpoint["device"])
                port = (device or {}).get("data", {}).get("ports", {}).get(endpoint["port"])
                if port is None:
                    raise ValueError("El equipo o puerto indicado no existe")
                compatible, reason = compatible_connection(wire["data"], port)
                if not compatible:
                    raise ValueError(reason)
                endpoint = {"device": device["id"], "port": endpoint["port"]}
                normalized.append(endpoint)
                key = (device["id"], endpoint["port"])
                if key in seen:
                    raise ValueError("Los dos extremos no pueden ocupar el mismo puerto")
                seen.add(key)
                for other in self.database.all():
                    if other["id"] != identifier and endpoint in other["data"].get("endpoints", []):
                        raise ValueError(f"El puerto ya está ocupado por {other['id']}")
            data = deepcopy(wire["data"])
            data["endpoints"] = normalized
            self.database.update(identifier, data)

    def port(self, identifier, expected, port, name, position):
        with locked_file(self.database.path):
            self._record(identifier, expected)
            self.database.edit_port(identifier, port, name=name, position=int(position))

    def delete(self, identifier, expected):
        with locked_file(self.database.path):
            self._record(identifier, expected)
            self.database.delete(identifier)
