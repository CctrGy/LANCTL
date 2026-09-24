"""Base de datos JSON con extensión .db para identificadores IDF."""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lanctl.apps.wire.idf import IDF, IDFSize
from lanctl.apps.wire.path import application_directory, application_path
from lanctl.apps.wire.topology import apply_prefix_defaults
from lanctl.apps.wire.xfile import atomic_write_bytes, locked_file, read, update_json, write_json

DATABASE_FORMAT = "LANWRE-IDF-DB"
DATABASE_VERSION = 1
DEFAULT_DATABASE_PATH = "data/lc/physical/idf.db"


def _empty_database() -> dict[str, Any]:
    return {"format": DATABASE_FORMAT, "version": DATABASE_VERSION, "prefixes": {}, "records": {}}


class IDFDatabaseManager:
    """Crea y administra una colección persistente de IDF únicos."""

    def __init__(self, path: str | Path = DEFAULT_DATABASE_PATH) -> None:
        requested = Path(path)
        self.path = application_path(requested)
        if self.path.suffix.casefold() != ".db":
            raise ValueError("la base de datos IDF debe usar la extensión .db")
        self._migrate_legacy_default(requested)
        self.create_database()

    def _migrate_legacy_default(self, requested: Path) -> None:
        """Copia la base histórica al almacén común la primera vez."""
        if requested.is_absolute() or requested.as_posix().casefold() != DEFAULT_DATABASE_PATH:
            return
        legacy = (application_directory() / "data" / "lw" / "idf.db").resolve()
        if not legacy.is_file() or legacy == self.path:
            return
        with locked_file(self.path):
            if not self.path.exists():
                atomic_write_bytes(self.path, legacy.read_bytes())

    def create_database(self) -> Path:
        """Crea una base vacía si todavía no existe y valida las existentes."""
        with locked_file(self.path):
            if not self.path.exists():
                write_json(self.path, _empty_database())
            database = read(self.path)
            self._validate_database(database)
            changed = False
            for record in database["records"].values():
                data = record.get("data") or {}
                updated = apply_prefix_defaults(record["prefix"], data)
                if updated != data:
                    record["data"] = updated
                    record["updated_at"] = self._timestamp()
                    changed = True
            if changed:
                write_json(self.path, database)
        return self.path.resolve()

    def create(
        self,
        prefix: str,
        *,
        size: IDFSize | str | None = None,
        number_width: int | None = None,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Reserva automáticamente el primer número libre de un prefijo."""
        normalized_prefix = prefix.strip().upper()
        template = IDF.build(normalized_prefix, 0, size, number_width=number_width)
        created: dict[str, Any] = {}

        def reserve(database: dict[str, Any]) -> None:
            nonlocal created
            self._validate_database(database)
            records = database["records"]
            maximum = 10**template.number_width - 1
            for number in range(maximum + 1):
                candidate = IDF.build(
                    normalized_prefix,
                    number,
                    size,
                    number_width=template.number_width,
                )
                if candidate.value not in records:
                    created = self._new_record(candidate, data)
                    records[candidate.value] = created
                    return
            raise OverflowError(f"no quedan números libres para el prefijo {normalized_prefix}")

        update_json(self.path, _empty_database, reserve)
        return deepcopy(created)

    def add(self, value: str | IDF, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Registra un IDF concreto y falla si ya está reservado."""
        identifier = value if isinstance(value, IDF) else IDF.parse(value)
        created = self._new_record(identifier, data)

        def insert(database: dict[str, Any]) -> None:
            self._validate_database(database)
            if identifier.value in database["records"]:
                raise ValueError(f"el IDF ya existe: {identifier.value}")
            database["records"][identifier.value] = created

        update_json(self.path, _empty_database, insert)
        return deepcopy(created)

    def get(self, value: str | IDF) -> dict[str, Any] | None:
        identifier = value if isinstance(value, IDF) else IDF.parse(value)
        record = self._load()["records"].get(identifier.value)
        return deepcopy(record) if record is not None else None

    def exists(self, value: str | IDF) -> bool:
        return self.get(value) is not None

    def all(self) -> list[dict[str, Any]]:
        records = self._load()["records"]
        return [deepcopy(records[key]) for key in sorted(records)]

    def list(self, prefix: str | None = None) -> list[dict[str, Any]]:
        """Lista todos los registros o únicamente los de un prefijo IDF."""
        records = self.all()
        if prefix is None:
            return records
        normalized = self._normalize_prefix(prefix)
        return [record for record in records if record["prefix"] == normalized]

    def list_group(self, group: str) -> list[dict[str, Any]]:
        """Filtra por grupo lógico sin acoplarlo al identificador físico."""
        from lanctl.apps.wire.topology import groups_for

        normalized = group.strip().upper()
        if not normalized:
            raise ValueError("el grupo no puede estar vacío")
        return [record for record in self.all() if normalized in groups_for(record)]

    def define_prefix(self, prefix: str, name: str, description: str = "") -> dict[str, str]:
        """Crea o actualiza la definición humana de un juego de letras."""
        normalized = self._normalize_prefix(prefix)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("el nombre del prefijo no puede estar vacío")
        definition = {
            "prefix": normalized,
            "name": name.strip(),
            "description": description.strip(),
        }

        def store(database: dict[str, Any]) -> None:
            self._validate_database(database)
            existing = database.setdefault("prefixes", {}).get(normalized, {})
            if existing.get("type_profile"):
                definition["type_profile"] = existing["type_profile"]
            database.setdefault("prefixes", {})[normalized] = definition

        update_json(self.path, _empty_database, store)
        return deepcopy(definition)

    def define_prefix_profile(
        self, prefix: str, profile: str, *, name: str = "", description: str = ""
    ) -> dict[str, str]:
        """Asigna a un juego de letras el perfil usado por futuros IDF."""
        from lanctl.apps.wire.topology import build_new_idf_data

        normalized = self._normalize_prefix(prefix)
        canonical = build_new_idf_data(profile)["subtype"]
        definition: dict[str, str] = {}

        def store(database: dict[str, Any]) -> None:
            nonlocal definition
            self._validate_database(database)
            existing = database.setdefault("prefixes", {}).get(normalized, {})
            definition = {
                "prefix": normalized,
                "name": name.strip() or existing.get("name") or canonical,
                "description": description.strip() or existing.get("description", ""),
                "type_profile": canonical,
            }
            database["prefixes"][normalized] = definition

        update_json(self.path, _empty_database, store)
        return deepcopy(definition)

    def get_prefix(self, prefix: str) -> dict[str, str] | None:
        definition = self._load().get("prefixes", {}).get(self._normalize_prefix(prefix))
        return deepcopy(definition) if definition is not None else None

    def prefixes(self) -> list[dict[str, str]]:
        definitions = self._load().get("prefixes", {})
        return [deepcopy(definitions[key]) for key in sorted(definitions)]

    def delete_prefix(self, prefix: str) -> dict[str, str]:
        normalized = self._normalize_prefix(prefix)
        deleted: dict[str, str] = {}

        def remove(database: dict[str, Any]) -> None:
            nonlocal deleted
            self._validate_database(database)
            try:
                deleted = database.setdefault("prefixes", {}).pop(normalized)
            except KeyError as error:
                raise KeyError(normalized) from error

        update_json(self.path, _empty_database, remove)
        return deepcopy(deleted)

    def update(self, value: str | IDF, data: dict[str, Any]) -> dict[str, Any]:
        """Sustituye los datos asociados sin cambiar el identificador."""
        identifier = value if isinstance(value, IDF) else IDF.parse(value)
        updated: dict[str, Any] = {}

        def replace(database: dict[str, Any]) -> None:
            nonlocal updated
            self._validate_database(database)
            if identifier.value not in database["records"]:
                raise KeyError(identifier.value)
            record = database["records"][identifier.value]
            old_ports = set((record.get("data") or {}).get("ports") or {})
            new_ports = set(data.get("ports") or {})
            removed_ports = old_ports - new_ports
            if removed_ports:
                connected = {
                    endpoint.get("port")
                    for candidate in database["records"].values()
                    if (candidate.get("data") or {}).get("type") == "wire"
                    for endpoint in (candidate.get("data") or {}).get("endpoints", [])
                    if isinstance(endpoint, dict)
                    and endpoint.get("device") == identifier.value
                    and endpoint.get("port") in removed_ports
                }
                if connected:
                    raise ValueError(
                        "desconecta antes los puertos: " + ", ".join(sorted(connected))
                    )
            record["data"] = deepcopy(data)
            record["updated_at"] = self._timestamp()
            updated = deepcopy(record)

        update_json(self.path, _empty_database, replace)
        return updated

    def edit_port(
        self, value: str | IDF, port: str, *, name: str | None = None, position: int | None = None
    ) -> dict[str, Any]:
        """Renombra o reordena un puerto y sus enlaces en una escritura atómica."""
        identifier = value if isinstance(value, IDF) else IDF.parse(value)
        updated: dict[str, Any] = {}

        def edit(database: dict[str, Any]) -> None:
            nonlocal updated
            self._validate_database(database)
            record = database["records"].get(identifier.value)
            if record is None:
                raise KeyError(identifier.value)
            data = record.get("data") or {}
            ports = data.get("ports") or {}
            if port not in ports:
                raise ValueError(f"puerto inexistente: {port}")
            new_name = name.strip() if name is not None else port
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", new_name):
                raise ValueError("el nombre del puerto debe usar letras, números, _ o -")
            if new_name != port and "FIBER" in {port, new_name}:
                raise ValueError("FIBER es un nombre fijo reservado para el puerto de fibra")
            if new_name != port and new_name in ports:
                raise ValueError(f"ya existe el puerto {new_name}")
            if position is not None and not 1 <= position <= len(ports):
                raise ValueError(f"la posición debe estar entre 1 y {len(ports)}")
            items = [
                (new_name if key == port else key, deepcopy(item)) for key, item in ports.items()
            ]
            if position is not None:
                moved = next(item for item in items if item[0] == new_name)
                items.remove(moved)
                items.insert(position - 1, moved)
            data["ports"] = dict(items)
            record["data"] = data
            record["updated_at"] = self._timestamp()
            if new_name != port:
                for candidate in database["records"].values():
                    wire_data = candidate.get("data") or {}
                    if wire_data.get("type") != "wire":
                        continue
                    for endpoint in wire_data.get("endpoints", []):
                        if (
                            endpoint.get("device") == identifier.value
                            and endpoint.get("port") == port
                        ):
                            endpoint["port"] = new_name
                            candidate["updated_at"] = self._timestamp()
            updated = deepcopy(record)

        update_json(self.path, _empty_database, edit)
        return updated

    def delete(self, value: str | IDF) -> dict[str, Any]:
        """Elimina un elemento y limpia las referencias físicas que deja atrás.

        Un equipo puede aparecer como extremo de varios cables o como ubicación
        de otro elemento. Todo se resuelve en la misma escritura atómica para
        que la topología no conserve enlaces colgantes.
        """
        identifier = value if isinstance(value, IDF) else IDF.parse(value)
        deleted: dict[str, Any] = {}

        def remove(database: dict[str, Any]) -> None:
            nonlocal deleted
            self._validate_database(database)
            try:
                deleted = database["records"].pop(identifier.value)
            except KeyError as error:
                raise KeyError(identifier.value) from error
            for record in database["records"].values():
                data = record.get("data")
                if not isinstance(data, dict):
                    continue
                if isinstance(data.get("endpoints"), list):
                    data["endpoints"] = [
                        endpoint
                        for endpoint in data["endpoints"]
                        if not isinstance(endpoint, dict)
                        or endpoint.get("device") != identifier.value
                    ]
                location = data.get("location")
                if isinstance(location, dict) and location.get("rack") == identifier.value:
                    location["rack"] = None
                record["updated_at"] = self._timestamp()

        update_json(self.path, _empty_database, remove)
        return deepcopy(deleted)

    def _load(self) -> dict[str, Any]:
        database = read(self.path)
        self._validate_database(database)
        return database

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        normalized = prefix.strip().upper()
        if not 2 <= len(normalized) <= 5 or not normalized.isascii() or not normalized.isalpha():
            raise ValueError("el prefijo debe contener entre 2 y 5 letras ASCII")
        return normalized

    @staticmethod
    def _new_record(identifier: IDF, data: dict[str, Any] | None) -> dict[str, Any]:
        timestamp = IDFDatabaseManager._timestamp()
        return {
            "id": identifier.value,
            "size": identifier.size.value if identifier.size else "custom",
            "prefix_width": identifier.prefix_width,
            "number_width": identifier.number_width,
            "prefix": identifier.prefix,
            "number": identifier.number,
            "data": apply_prefix_defaults(identifier.prefix, data),
            "created_at": timestamp,
            "updated_at": timestamp,
        }

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _validate_database(database: Any) -> None:
        if not isinstance(database, dict):
            raise ValueError("la base de datos IDF debe ser un objeto JSON")
        if database.get("format") != DATABASE_FORMAT:
            raise ValueError("el archivo no es una base de datos IDF de LANWRE")
        if database.get("version") != DATABASE_VERSION:
            raise ValueError("versión de base de datos IDF no compatible")
        records = database.get("records")
        if not isinstance(records, dict):
            raise ValueError("el campo records de la base de datos no es válido")
        for key, record in records.items():
            if not IDF.is_valid(key) or not isinstance(record, dict) or record.get("id") != key:
                raise ValueError(f"registro IDF no válido: {key}")
        prefixes = database.get("prefixes", {})
        if not isinstance(prefixes, dict):
            raise ValueError("el campo prefixes de la base de datos no es válido")
        for key, definition in prefixes.items():
            if not isinstance(definition, dict) or definition.get("prefix") != key:
                raise ValueError(f"definición de prefijo no válida: {key}")
