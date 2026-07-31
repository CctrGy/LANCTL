from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from app.core.paths import application_directory


CURRENT_DATA_NAME = "lc"
LEGACY_DATA_NAME = "als"


def ensure_data_layout() -> Path:
    """Migra data/als a data/lc sin sobrescribir conflictos silenciosamente."""
    data_root = application_directory() / "data"
    current = data_root / CURRENT_DATA_NAME
    legacy = data_root / LEGACY_DATA_NAME
    if not legacy.exists():
        current.mkdir(parents=True, exist_ok=True)
        return current.resolve()
    if not current.exists():
        data_root.mkdir(parents=True, exist_ok=True)
        legacy.replace(current)
        return current.resolve()

    backup_root = current / "migration-backup-als"
    for source in sorted(legacy.rglob("*")):
        if source.is_dir():
            continue
        relative = source.relative_to(legacy)
        destination = current / relative
        if not destination.exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.replace(destination)
            continue
        if _same_file(source, destination):
            source.unlink()
            continue
        backup = backup_root / relative
        backup.parent.mkdir(parents=True, exist_ok=True)
        counter = 1
        while backup.exists():
            backup = backup.with_name(f"{backup.stem}.{counter}{backup.suffix}")
            counter += 1
        source.replace(backup)
    shutil.rmtree(legacy)
    return current.resolve()


def migrate_config_paths(value):
    """Convierte rutas históricas dentro de objetos JSON de configuración."""
    if isinstance(value, dict):
        return {key: migrate_config_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [migrate_config_paths(item) for item in value]
    if isinstance(value, str):
        return value.replace("data/als/", "data/lc/").replace("data\\als\\", "data\\lc\\")
    return value


def _same_file(first: Path, second: Path) -> bool:
    if first.stat().st_size != second.stat().st_size:
        return False
    return _digest(first) == _digest(second)


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
