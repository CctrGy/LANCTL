"""VLF adapter for the shared IDF domain, independent of CLI/TUI/GUI.

The existing IDF/CPD domain validators remain authoritative. This adapter only
versions the archive envelope and locates the project's working copy.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lanctl.core.file_transaction import atomic_write_json, locked_file, locked_files

ARCHIVE_ENTRY = "devices/physical.json"


def workspace_path(database: Path) -> Path:
    return database.parent / "physical" / "idf.db"


def empty_inventory() -> dict:
    from lanctl.apps.wire.idf.database import DATABASE_FORMAT, DATABASE_VERSION

    return {"format": DATABASE_FORMAT, "version": DATABASE_VERSION, "prefixes": {}, "records": {}}


def validate_inventory(document: object) -> dict:
    from lanctl.apps.rack.organization import organization
    from lanctl.apps.wire.idf.database import IDFDatabaseManager

    IDFDatabaseManager._validate_database(document)
    if type(document["version"]) is not int:
        raise ValueError("Versión del inventario físico no válida")
    for record in document["records"].values():
        if not isinstance(record.get("data"), dict):
            raise ValueError("Datos del elemento físico no válidos")
    organization(document)
    return document


def decode_archive(raw: bytes) -> dict:
    envelope = json.loads(raw)
    if (
        not isinstance(envelope, dict)
        or type(envelope.get("schemaVersion")) is not int
        or envelope["schemaVersion"] != 1
    ):
        raise ValueError("Esquema de inventario físico VLF no compatible")
    return validate_inventory(envelope.get("inventory"))


def load_inventory(path: Path) -> dict:
    with locked_file(path):
        return validate_inventory(json.loads(path.read_text(encoding="utf-8")))


def require_existing_workspace_inventory(path: Path) -> None:
    """Never recreate a missing, previously materialized project as empty."""
    if (
        path.exists()
        or path.name.casefold() != "idf.db"
        or path.parent.name.casefold() != "physical"
    ):
        return
    metadata = path.parent.parent / "workspace.json"
    if metadata.is_file():
        document = json.loads(metadata.read_text(encoding="utf-8"))
        if isinstance(document, dict) and document.get("physicalSchemaVersion") == 1:
            raise FileNotFoundError(
                "Falta el inventario físico del proyecto; restaura una copia o recarga "
                "explícitamente el VLF antes de editar. No se ha creado una base vacía."
            )


def fingerprint(logical: str, database: Path) -> str:
    path = workspace_path(database)
    if not path.exists():
        return logical
    document = load_inventory(path)
    # Preserve historical logical fingerprints for an exactly empty inventory.
    if document == empty_inventory():
        return logical
    value = {"logical": logical, "physical": document}
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def import_inventory(source: str | Path, expected_project) -> dict:
    """Copy a legacy inventory only into an explicitly selected empty project."""
    from lanctl.core.config import load_config
    from lanctl.core.paths import application_path
    from lanctl.core.project_context import project_operation, require_project
    from lanctl.core.projects.physical_mutations import physical_mutation

    with project_operation():
        require_project(expected_project)
        settings = load_config()
        workspace = settings.get("projectWorkspace")
        if not settings.get("activeProject") or not isinstance(workspace, dict):
            raise ValueError("Selecciona primero el proyecto que recibirá el inventario físico")
        destination = workspace_path(Path(workspace["database"]))
        original = application_path(source)
        if original.resolve() == destination.resolve():
            raise ValueError("El origen ya es el inventario del proyecto activo")
        with physical_mutation(destination), locked_files((original, destination)):
            document = load_inventory(original)
            if load_inventory(destination) != empty_inventory():
                raise ValueError(
                    "El proyecto ya tiene inventario físico; importa en un proyecto vacío"
                )
            atomic_write_json(destination, document)
        return {
            "records": len(document["records"]),
            "source": str(original),
            "project": settings["activeProject"],
        }
