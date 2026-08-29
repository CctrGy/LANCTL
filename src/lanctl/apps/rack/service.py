"""Consultas de solo lectura sobre los racks administrados por LANWIRE."""

from __future__ import annotations

from lanctl.apps.wire.idf.database import IDFDatabaseManager


class RackService:
    def __init__(self, database_path: str) -> None:
        self.database = IDFDatabaseManager(database_path)

    def list(self) -> list[dict]:
        records = self.database.all()
        return [self.describe(record, records) for record in records if self._is_rack(record)]

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
                }
            )
        occupants.sort(key=lambda item: (-(int(item["unit"] or 0)), item["id"]))
        return {
            "id": rack["id"],
            "name": data.get("name") or data.get("alias") or rack["id"],
            "units": int(data.get("units") or data.get("size_units") or data.get("height") or 42),
            "description": data.get("description", ""),
            "location": data.get("location", {}),
            "layout": data.get("layout", []),
            "occupants": occupants,
        }
