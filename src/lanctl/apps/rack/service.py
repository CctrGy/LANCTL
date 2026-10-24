"""Consultas de racks y organización CPD del inventario compartido."""

from __future__ import annotations

from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.xfile import locked_file
from lanctl.core.physical_placement import location_status, span, validate_location, with_location
from lanctl.core.projects.physical_mutations import physical_edit


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
                "elements": self.elements(),
                "storage": str(self.database.path),
                **snapshot(self.database),
                "skinProfiles": profiles(),
            }

    def elements(self):
        from lanctl.apps.wire.gui_service import revision

        records = self.database.all()
        index = {r["id"]: r for r in records}
        return [
            {**r, "revision": revision(r), "placement": location_status(r["data"], index)}
            for r in records
        ]

    @physical_edit
    def edit_element(self, expected, operation, identifier, values):
        """One inventory revision check and transaction shared with LANWIRE."""
        from lanctl.apps.rack.organization import token
        from lanctl.apps.wire.gui_service import WireGuiService, revision
        from lanctl.apps.wire.xfile import read

        with locked_file(self.database.path):
            document = read(self.database.path)
            self.database._validate_database(document)
            if token(document) != expected:
                raise ValueError("El inventario cambió; actualiza antes de editar el elemento")
            service = WireGuiService(self.database.path)
            if operation == "import-tray":
                return self._convert_tray(expected, identifier, values)
            if operation == "create":
                return service.create(values)
            record = self.database.get(identifier)
            if record is None:
                raise ValueError("El elemento ya no existe")
            current = revision(record)
            if operation == "update":
                service.update(identifier, current, values)
            elif operation == "delete":
                service.delete(identifier, current)
            elif operation == "port":
                service.port(
                    identifier, current, values["port"], values["name"], values["position"]
                )
            elif operation == "connect":
                service.connect(identifier, current, values["endpoints"])
            else:
                raise ValueError("Operación de elemento no válida")
            return {"id": identifier}

    def _convert_tray(self, expected, identifier, values):
        from lanctl.apps.rack.organization import token
        from lanctl.apps.wire.idf import IDF
        from lanctl.apps.wire.xfile import update_json
        from lanctl.core.physical_placement import apply_placement

        result = {}

        def convert(document):
            self.database._validate_database(document)
            if token(document) != expected:
                raise ValueError("El inventario cambió; actualiza antes de convertir la bandeja")
            rack = document["records"].get(identifier)
            if not rack or not self._is_rack(rack):
                raise ValueError("Selecciona un rack existente")
            layout = rack["data"].get("layout", [])
            item = next(
                (
                    i
                    for i in layout
                    if i.get("kind") == "tray"
                    and not i.get("idf")
                    and i.get("unit") == values.get("unit")
                ),
                None,
            )
            if item is None:
                raise ValueError("La bandeja heredada ya no existe")
            data = apply_placement(
                {"type": "tray", "name": item.get("label") or "Bandeja", "legacyRackLayout": item},
                {
                    "rack": identifier,
                    "unit": item["unit"],
                    "in_rack": True,
                    "heightU": item.get("height", 1),
                },
            )
            candidate = next(
                (
                    IDF.build("TR", n)
                    for n in range(100)
                    if IDF.build("TR", n).value not in document["records"]
                ),
                None,
            )
            if candidate is None:
                raise ValueError("No quedan identificadores de bandeja TR disponibles")
            layout.remove(item)
            record = self.database._new_record(candidate, data)
            validate_location(list(document["records"].values()), candidate.value, data)
            document["records"][candidate.value] = record
            rack["updated_at"] = self.database._timestamp()
            result["id"] = candidate.value

        update_json(self.database.path, dict, convert)
        return result

    def destinations(self, identifier, height):
        from lanctl.apps.wire.gui_service import WireGuiService

        with locked_file(self.database.path):
            records = self.database.all()
            record = self.database.get(identifier)
            if not record or self._is_rack(record) or record["data"].get("type") == "wire":
                raise ValueError("Selecciona un elemento físico")
            data = WireGuiService._fields(record["data"], {"heightU": height})
            choices = []
            index = {r["id"]: r for r in records}
            for rack in records:
                if not self._is_rack(rack):
                    continue
                for unit in range(1, 53):
                    candidate = with_location(data, rack=rack["id"], in_rack=True, unit=unit)
                    try:
                        validate_location(index, identifier, candidate)
                    except ValueError:
                        continue
                    choices.append({"rack": rack["id"], "unit": unit})
            return {"destinations": choices}

    @physical_edit
    def organize(self, expected, operation, values):
        from lanctl.apps.rack.organization import mutate

        return mutate(self.database, expected, operation, values)

    @physical_edit
    def set_appearance(self, expected, identifier, values):
        from lanctl.apps.rack.skins import save

        return save(self.database, expected, identifier, values)

    @physical_edit
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
        from lanctl.core.rack_dimensions import dimension_status

        data = rack.get("data") or {}
        occupants = []
        index = {r["id"]: r for r in records}
        for record in records:
            item = record.get("data") or {}
            location = location_status(item, index)
            if str(location.get("rack", "")).casefold() != rack["id"].casefold():
                continue
            occupants.append(
                {
                    "id": record["id"],
                    "unit": location.get("unit") if location["kind"] == "inside" else 0,
                    "placement": location,
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
