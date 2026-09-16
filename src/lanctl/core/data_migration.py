from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path

from lanctl.core.file_transaction import (
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    locked_file,
)
from lanctl.core.paths import (
    application_directory,
    application_path,
    data_root,
    is_portable_install,
    secret_root,
)

LAYOUT_DIRECTORIES = (
    "config",
    "config/icons",
    "config/languages",
    "database",
    "logs",
    "monitoring",
    "plugins",
    "plugins/storage",
    "projects",
    "projects/workspaces",
    "automation",
)

INITIAL_JSON_FILES = {
    "data/lc/projects/workspaces/default/database/devices.json": [],
    "data/lc/projects/workspaces/default/database/groups.json": [
        {
            "name": "BASIC",
            "description": "Elementos basicos de la LAN",
            "members": [],
            "editable": False,
        }
    ],
    "data/lc/recurrent-elements.json": {
        "schemaVersion": 1,
        "documentType": "lanctl.recurrent-elements",
        "elements": [],
    },
    "data/lc/plugins.registry": {},
    "data/lc/wol-sequences.json": {
        "schemaVersion": 1,
        "documentType": "lanctl.wol-sequences",
        "sequences": {},
        "runs": {},
    },
    "data/lc/projects/workspaces/default/monitoring/sessions.json": {},
    "data/lc/projects/workspaces/default/monitoring/incidents.json": [],
    "data/lc/projects/workspaces/default/monitoring/profiles.json": {
        "schemaVersion": 1,
        "documentType": "lanctl.monitor-profiles",
        "profiles": {},
    },
    "data/lc/projects/workspaces/default/monitoring/assignments.json": {
        "schemaVersion": 1,
        "documentType": "lanctl.monitor-assignments",
        "assignments": [],
    },
    "data/lc/cisco_profiles.json": {
        "schemaVersion": 1,
        "documentType": "lanctl.cisco-profiles",
        "profiles": [],
    },
    "data/lc/projects/workspaces/default/physical/idf.db": {
        "format": "LANWRE-IDF-DB",
        "version": 1,
        "prefixes": {},
        "records": {},
    },
}


def ensure_data_layout() -> Path:
    """Crea el layout mutable y copia datos legacy sin escribir junto al EXE."""
    root = data_root()
    for name in LAYOUT_DIRECTORIES:
        (root / name).mkdir(parents=True, exist_ok=True)
    secret_root().mkdir(parents=True, exist_ok=True)
    marker = root / "config" / "migration-v2.complete"
    with locked_file(marker):
        _migrate_misplaced_root_state(root)
        sources = [] if marker.exists() else _legacy_sources(root)
        conflicts = []
        for source in sources:
            conflicts.extend(_copy_legacy_tree(source, root))
        if conflicts:
            joined = ", ".join(str(path) for path in conflicts[:5])
            raise ValueError(f"migración detenida por conflictos de datos legacy: {joined}")
        _create_initial_files()
        _upgrade_structured_documents()
        from lanctl.core.persistence import migrate_schema

        migrate_schema(root / "config" / "storage-schema.json")
        if not marker.exists():
            atomic_write_text(marker, "LANCTL-DATA-V2\n", encoding="ascii")
    return root.resolve()


def _upgrade_structured_documents() -> None:
    """Migra catálogos de configuración legacy a documentos versionados."""

    upgrades = {
        "data/lc/recurrent-elements.json": _upgrade_recurrent_elements,
        "data/lc/wol-sequences.json": _upgrade_wol_sequences,
        "data/lc/cisco_profiles.json": _upgrade_cisco_profiles,
        "data/lc/projects/workspaces/default/monitoring/profiles.json": (
            lambda value: _upgrade_named_collection(
                value, "lanctl.monitor-profiles", "profiles", {}
            )
        ),
        "data/lc/projects/workspaces/default/monitoring/assignments.json": (
            lambda value: _upgrade_named_collection(
                value, "lanctl.monitor-assignments", "assignments", []
            )
        ),
    }
    for resource, upgrade in upgrades.items():
        path = application_path(resource)
        if not path.exists():
            continue
        with locked_file(path):
            import json

            current = json.loads(path.read_text(encoding="utf-8"))
            normalized = upgrade(current)
            if normalized != current:
                atomic_write_json(path, normalized)


def _upgrade_named_collection(value, document_type: str, key: str, empty):
    if isinstance(value, dict) and "schemaVersion" in value:
        return value
    collection = value.get(key, empty) if isinstance(value, dict) else value
    if collection in ({}, []) and collection != empty:
        collection = deepcopy(empty)
    return {
        "schemaVersion": 1,
        "documentType": document_type,
        key: collection,
    }


def _upgrade_recurrent_elements(value):
    if isinstance(value, dict) and "schemaVersion" in value:
        return value
    elements = value if isinstance(value, list) else value.get("elements", [])
    return {
        "schemaVersion": 1,
        "documentType": "lanctl.recurrent-elements",
        "elements": elements,
    }


def _upgrade_wol_sequences(value):
    if isinstance(value, dict) and "schemaVersion" in value:
        return value
    value = value if isinstance(value, dict) else {}
    return {
        "schemaVersion": 1,
        "documentType": "lanctl.wol-sequences",
        "sequences": value.get("sequences", {}),
        "runs": value.get("runs", {}),
    }


def _upgrade_cisco_profiles(value):
    if isinstance(value, dict) and "schemaVersion" in value:
        return value
    profiles = value.get("profiles", value) if isinstance(value, dict) else value
    if profiles == {}:
        profiles = []
    return {
        "schemaVersion": 1,
        "documentType": "lanctl.cisco-profiles",
        "profiles": profiles,
    }


def _migrate_misplaced_root_state(root: Path) -> None:
    """Recupera estado creado en la raíz por versiones instaladas anteriores."""

    source = root / "recurrent-elements.json"
    destination = root / "automation" / "recurrent-elements.json"
    if not source.is_file() or destination.exists():
        return
    with locked_file(destination):
        if not destination.exists():
            atomic_write_bytes(destination, source.read_bytes())


def _create_initial_files() -> None:
    """Crea los JSON base atómicamente y nunca sobrescribe datos existentes."""
    from lanctl.core.config import DOCUMENT_DEFAULTS

    initial_files = {application_path("data/lc/.config"): deepcopy(DOCUMENT_DEFAULTS)}
    initial_files.update(
        (application_path(name), deepcopy(value)) for name, value in INITIAL_JSON_FILES.items()
    )
    for path, value in initial_files.items():
        with locked_file(path):
            if not path.exists():
                atomic_write_json(path, value)


def _legacy_sources(destination: Path) -> list[Path]:
    candidates = []
    source_root = application_directory() / "data"
    for name in ("lc", "als"):
        candidate = source_root / name
        if candidate.exists() and candidate.resolve() != destination.resolve():
            candidates.append(candidate)
    if is_portable_install():
        old = application_directory() / "data" / "lc"
        if old.exists() and old not in candidates:
            candidates.append(old)
    return candidates


def _copy_legacy_tree(source: Path, destination_root: Path) -> list[Path]:
    conflicts = []
    for item in sorted(source.rglob("*")):
        if item.is_dir():
            continue
        relative = item.relative_to(source)
        if relative.parts and (
            relative.parts[0].startswith(".merge-backup-")
            or relative.parts[0].startswith("migration-backup-")
        ):
            continue
        destination = application_path(Path("data/lc") / relative)
        with locked_file(destination):
            if destination.exists():
                if not _same_file(item, destination):
                    conflicts.append(relative)
                continue
            atomic_write_bytes(destination, item.read_bytes())
    return conflicts


def migrate_config_paths(value):
    """Normaliza rutas históricas; application_path aplica el layout final."""
    if isinstance(value, dict):
        return {key: migrate_config_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [migrate_config_paths(item) for item in value]
    if isinstance(value, str):
        return value.replace("data/als/", "data/lc/").replace("data\\als\\", "data\\lc\\")
    return value


def _same_file(first: Path, second: Path) -> bool:
    return first.stat().st_size == second.stat().st_size and _digest(first) == _digest(second)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
