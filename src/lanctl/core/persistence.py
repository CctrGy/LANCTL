from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lanctl.core.file_transaction import atomic_write_json, locked_files

STORAGE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class StorageCheck:
    path: str
    exists: bool
    valid: bool
    kind: str
    detail: str = ""


def create_backup(path: str | Path, *, directory: str | Path | None = None) -> Path:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    target_root = Path(directory) if directory else source.parent / "backups"
    target_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = target_root / f"{source.name}.{timestamp}.bak"
    with locked_files((source, target)):
        shutil.copy2(source, target)
    return target


def restore_backup(path: str | Path, backup: str | Path) -> Path:
    target, source = Path(path), Path(backup)
    if not source.is_file():
        raise FileNotFoundError(source)
    if target.suffix.casefold() == ".json":
        json.loads(source.read_text(encoding="utf-8"))
    with locked_files((target, source)):
        from lanctl.core.file_transaction import atomic_write_bytes

        atomic_write_bytes(target, source.read_bytes())
    return target


def diagnose_storage(paths: list[str | Path]) -> list[StorageCheck]:
    checks: list[StorageCheck] = []
    resolved: set[str] = set()
    for value in paths:
        path = Path(value).resolve()
        key = str(path).casefold()
        if key in resolved:
            continue
        resolved.add(key)
        if not path.exists():
            checks.append(StorageCheck(str(path), False, False, "missing", "no existe"))
            continue
        if not path.is_file():
            checks.append(StorageCheck(str(path), True, False, "unsupported", "no es un archivo"))
            continue
        try:
            payload = path.read_bytes()
            if path.suffix.casefold() in {".json", ".registry"} or path.name == ".config":
                json.loads(payload.decode("utf-8"))
                kind = "json"
            elif payload.startswith(b"SQLite format 3\x00"):
                kind = "sqlite"
            else:
                kind = "binary"
            checks.append(
                StorageCheck(str(path), True, True, kind, hashlib.sha256(payload).hexdigest())
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            checks.append(StorageCheck(str(path), True, False, "corrupt", str(error)))
    return checks


def export_storage(paths: list[str | Path], destination: str | Path) -> Path:
    target = Path(destination)
    files = [Path(path).resolve() for path in paths if Path(path).is_file()]
    if not files:
        raise ValueError("no hay archivos persistentes para exportar")
    common = Path(__import__("os").path.commonpath([str(path.parent) for path in files]))
    manifest: dict[str, Any] = {
        "schemaVersion": STORAGE_SCHEMA_VERSION,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "files": {},
    }
    target.parent.mkdir(parents=True, exist_ok=True)
    with locked_files(tuple([*files, target])):
        with tempfile.NamedTemporaryFile(delete=False, dir=target.parent, suffix=".tmp") as stream:
            temporary = Path(stream.name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    name = path.relative_to(common).as_posix()
                    payload = path.read_bytes()
                    archive.writestr(f"data/{name}", payload)
                    manifest["files"][name] = hashlib.sha256(payload).hexdigest()
                archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    verify_export(target)
    return target


def verify_export(path: str | Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("schemaVersion") != STORAGE_SCHEMA_VERSION:
            raise ValueError("versión de exportación incompatible")
        for name, expected in manifest.get("files", {}).items():
            actual = hashlib.sha256(archive.read(f"data/{name}")).hexdigest()
            if actual != expected:
                raise ValueError(f"hash incorrecto en la exportación: {name}")
    return manifest


def schema_document() -> dict[str, Any]:
    return {
        "schemaVersion": STORAGE_SCHEMA_VERSION,
        "scopes": {
            "global": "recursos inmutables instalados con LANCTL",
            "user": "configuración, credenciales, plugins y registros del ámbito activo",
            "project": "workspace y archivo VLF seleccionados explícitamente",
        },
    }


def write_schema_marker(path: str | Path) -> Path:
    atomic_write_json(path, schema_document())
    return Path(path)


def migrate_schema(path: str | Path) -> Path | None:
    """Actualiza el marcador con backup previo y rechaza esquemas futuros."""

    marker = Path(path)
    if not marker.exists():
        write_schema_marker(marker)
        return None
    try:
        current = json.loads(marker.read_text(encoding="utf-8"))
        version = int(current.get("schemaVersion", 0))
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        raise ValueError(f"marcador de esquema corrupto: {marker}") from error
    if version > STORAGE_SCHEMA_VERSION:
        raise ValueError(
            f"esquema {version} incompatible; esta versión admite {STORAGE_SCHEMA_VERSION}"
        )
    if version == STORAGE_SCHEMA_VERSION:
        return None
    backup = create_backup(marker, directory=marker.parent / "migration-backups")
    write_schema_marker(marker)
    return backup


def checks_as_dict(checks: list[StorageCheck]) -> list[dict[str, Any]]:
    return [asdict(check) for check in checks]
