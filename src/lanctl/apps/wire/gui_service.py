"""Structured desktop operations on the same IDF database as CLI/TUI."""

import hashlib
import ipaddress
import json
from copy import deepcopy

from lanctl.apps.wire.idf import IDF
from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.topology import (
    build_new_idf_data,
    build_ports,
    compatible_connection,
    groups_for,
)
from lanctl.core.file_transaction import locked_file
from lanctl.core.physical_placement import apply_placement, location_status, with_location
from lanctl.core.projects.physical_mutations import physical_edit


def revision(record):
    return hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()


class WireGuiService:
    def __init__(self, path):
        self.database = IDFDatabaseManager(path)

    def snapshot(self):
        from lanctl.apps.rack.organization import snapshot

        with locked_file(self.database.path):
            records = self.database.all()
            index = {r["id"]: r for r in records}
            return {
                "records": [
                    {
                        **r,
                        "revision": revision(r),
                        "filterGroups": sorted(groups_for(r)),
                        "placement": location_status(r["data"], index),
                    }
                    for r in records
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
        result = apply_placement(result, values)
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
            from lanctl.core.rack_dimensions import validate_height

            result["units"] = validate_height(values["units"])
            for alias in ("size_units", "height"):
                if alias in result:
                    result[alias] = result["units"]
        if "widthInches" in values:
            from lanctl.core.rack_dimensions import validate_width

            result["rackDimensions"] = {
                "schemaVersion": 1,
                "widthInches": validate_width(values["widthInches"]),
            }
        return result

    @physical_edit
    def create(self, values):
        kind = values["kind"]
        if kind == "rack":
            from lanctl.core.rack_dimensions import validate_height

            units = validate_height(values.get("units", 42))
            data = {"type": "rack", "units": units}
        elif kind == "tray":
            data = {"type": "tray", "ports": {}}
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
        if kind not in {"rack", "wire.copper", "wire.fiber", "wire.dac"} and "location" not in data:
            data = with_location(data)
        with locked_file(self.database.path):
            if "endpoints" in values:
                data["endpoints"] = self._endpoints(data, values["endpoints"])
            record = self.database.create(values["prefix"], data=data)
        return {"id": record["id"]}

    @physical_edit
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
            self.database.update(identifier, data)

    @physical_edit
    def connect(self, identifier, expected, endpoints):
        with locked_file(self.database.path):
            wire = self._record(identifier, expected)
            data = deepcopy(wire["data"])
            data["endpoints"] = self._endpoints(data, endpoints, identifier)
            self.database.update(identifier, data)

    def _endpoints(self, data, endpoints, identifier=None):
        """Shared validation; caller holds the inventory lock through commit."""
        if not isinstance(endpoints, list) or len(endpoints) > 2:
            raise ValueError("Un cable admite como máximo dos extremos")
        if data.get("type") != "wire":
            raise ValueError("Selecciona un cable")
        if data.get("source") and len(endpoints) > 1:
            raise ValueError("El suministro externo ya ocupa uno de los extremos del cable")
        records = self.database.all()
        index = {r["id"]: r for r in records}
        seen = set()
        normalized = []
        for endpoint in endpoints:
            if not isinstance(endpoint, dict) or not all(
                isinstance(endpoint.get(key), str) for key in ("device", "port")
            ):
                raise ValueError("Cada extremo necesita un equipo y un puerto de texto")
            device = index.get(IDF.parse(endpoint["device"]).value)
            port = (device or {}).get("data", {}).get("ports", {}).get(endpoint["port"])
            if port is None:
                raise ValueError("El equipo o puerto indicado no existe")
            compatible, reason = compatible_connection(data, port)
            if not compatible:
                raise ValueError(reason)
            endpoint = {"device": device["id"], "port": endpoint["port"]}
            key = (device["id"], endpoint["port"])
            if key in seen:
                raise ValueError("Los dos extremos no pueden ocupar el mismo puerto")
            seen.add(key)
            for other in records:
                if other["id"] != identifier and endpoint in other["data"].get("endpoints", []):
                    raise ValueError(f"El puerto ya está ocupado por {other['id']}")
            normalized.append(endpoint)
        return normalized

    @physical_edit
    def port(self, identifier, expected, port, name, position):
        with locked_file(self.database.path):
            self._record(identifier, expected)
            self.database.edit_port(identifier, port, name=name, position=int(position))

    @physical_edit
    def delete(self, identifier, expected):
        with locked_file(self.database.path):
            self._record(identifier, expected)
            self.database.delete(identifier)
