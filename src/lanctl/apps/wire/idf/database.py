"""Base de datos JSON con extensión .db para identificadores IDF."""

from __future__ import annotations

import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lanctl.apps.wire.idf import IDF, IDFSize
from lanctl.apps.wire.path import application_directory, application_path
from lanctl.apps.wire.xfile import read, update_json, write_json

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
        if self.path.exists() or not legacy.is_file() or legacy == self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, self.path)

    def create_database(self) -> Path:
        """Crea una base vacía si todavía no existe y valida las existentes."""
        if not self.path.exists():
            write_json(self.path, _empty_database())
        self._load()
        return self.path.resolve()

    def create(
        self, prefix: str, *, size: IDFSize | str | None = None, data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Reserva automáticamente el primer número libre de un prefijo."""
        normalized_prefix = prefix.strip().upper()
        resolved_size = IDF.build(normalized_prefix, 0, size).size
        created: dict[str, Any] = {}

        def reserve(database: dict[str, Any]) -> None:
            nonlocal created
            self._validate_database(database)
            records = database["records"]
            maximum = 99 if resolved_size is IDFSize.SHORT else 9999
            for number in range(maximum + 1):
                candidate = IDF.build(normalized_prefix, number, resolved_size)
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
            database.setdefault("prefixes", {})[normalized] = definition

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
            record["data"] = deepcopy(data)
            record["updated_at"] = self._timestamp()
            updated = deepcopy(record)

        update_json(self.path, _empty_database, replace)
        return updated

    def delete(self, value: str | IDF) -> dict[str, Any]:
        identifier = value if isinstance(value, IDF) else IDF.parse(value)
        deleted: dict[str, Any] = {}

        def remove(database: dict[str, Any]) -> None:
            nonlocal deleted
            self._validate_database(database)
            try:
                deleted = database["records"].pop(identifier.value)
            except KeyError as error:
                raise KeyError(identifier.value) from error

        update_json(self.path, _empty_database, remove)
        return deepcopy(deleted)

    def _load(self) -> dict[str, Any]:
        database = read(self.path)
        self._validate_database(database)
        return database

    @staticmethod
    def _normalize_prefix(prefix: str) -> str:
        normalized = prefix.strip().upper()
        if len(normalized) not in (2, 4) or not normalized.isascii() or not normalized.isalpha():
            raise ValueError("el prefijo debe contener 2 o 4 letras ASCII")
        return normalized

    @staticmethod
    def _new_record(identifier: IDF, data: dict[str, Any] | None) -> dict[str, Any]:
        timestamp = IDFDatabaseManager._timestamp()
        return {
            "id": identifier.value,
            "size": identifier.size.value,
            "prefix": identifier.prefix,
            "number": identifier.number,
            "data": deepcopy(data or {}),
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
