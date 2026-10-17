"""Consultas de racks y organización CPD del inventario compartido."""

from __future__ import annotations

from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.xfile import locked_file


class RackService:
    def __init__(self, database_path: str) -> None:
        self.database = IDFDatabaseManager(database_path)

    def list(self) -> list[dict]:
        records = self.database.all()
        return [self.describe(record, records) for record in records if self._is_rack(record)]

    def snapshot(self):
        from lanctl.apps.rack.organization import snapshot
        from lanctl.apps.rack.skins import profiles

        with locked_file(self.database.path):
            return {
                "records": self.list(),
                "storage": str(self.database.path),
                **snapshot(self.database),
                "skinProfiles": profiles(),
            }

    def organize(self, expected, operation, values):
        from lanctl.apps.rack.organization import mutate

        return mutate(self.database, expected, operation, values)

    def set_appearance(self, expected, identifier, values):
        from lanctl.apps.rack.skins import save

        return save(self.database, expected, identifier, values)

    def set_dimensions(self, expected, identifier, values):
        from lanctl.apps.rack.organization import token
        from lanctl.apps.wire.xfile import read
        from lanctl.core.rack_dimensions import with_dimensions

        if not isinstance(values, dict) or set(values) != {"units", "widthInches"}:
            raise ValueError("Indica altura y ancho de montaje del rack")
        with locked_file(self.database.path):
            document = read(self.database.path)
            self.database._validate_database(document)
            if token(document) != expected:
                raise ValueError("El inventario cambió; actualiza antes de editar las dimensiones")
            record = self.database.get(identifier)
            if record is None or not self._is_rack(record):
                raise ValueError("Selecciona un armario rack existente")
            data = with_dimensions(record["data"], values["units"], values["widthInches"])
            self.database.update(identifier, data)
        return {"id": record["id"]}

    def get(self, identifier: str) -> dict:
        records = self.database.all()
        rack = next(
            (record for record in records if record["id"].casefold() == identifier.casefold()),
            None,
        )
        if rack is None or not self._is_rack(rack):
            raise ValueError(f"rack no encontrado: {identifier}")
        return self.describe(rack, records)

    @staticmethod
    def _is_rack(record: dict) -> bool:
        data = record.get("data") or {}
        return data.get("type") == "rack" or record.get("prefix") == "RK"

    @staticmethod
    def describe(rack: dict, records: list[dict]) -> dict:
        from lanctl.apps.rack.skins import span
        from lanctl.core.rack_dimensions import dimension_status

        data = rack.get("data") or {}
        occupants = []
        for record in records:
            item = record.get("data") or {}
            location = item.get("location") or {}
            if str(location.get("rack", "")).casefold() != rack["id"].casefold():
                continue
            occupants.append(
                {
                    "id": record["id"],
                    "unit": location.get("unit"),
                    "name": item.get("name") or item.get("alias") or "",
                    "type": item.get("type", "element"),
                    "description": item.get("description", ""),
                    "data": item,
                    "span": span(item),
                    "connectedPorts": [
                        end.get("port")
                        for wire in records
                        if (wire.get("data") or {}).get("type") == "wire"
                        for end in wire["data"].get("endpoints", [])
                        if end.get("device") == record["id"]
                    ],
                }
            )
        occupants.sort(key=lambda item: (-(int(item["unit"] or 0)), item["id"]))
        dimensions = dimension_status(data)
        return {
            "id": rack["id"],
            "name": data.get("name") or data.get("alias") or rack["id"],
            "units": dimensions["heightU"],
            "widthInches": dimensions["widthInches"],
            "dimensions": dimensions,
            "description": data.get("description", ""),
            "location": data.get("location", {}),
            "layout": data.get("layout", []),
            "occupants": occupants,
        }
