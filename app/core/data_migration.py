from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from app.core.paths import (
    application_directory,
    application_path,
    data_root,
    is_portable_install,
    secret_root,
)

LAYOUT_DIRECTORIES = (
    "config",
    "database",
    "logs",
    "monitoring",
    "plugins",
    "projects",
    "automation",
)


def ensure_data_layout() -> Path:
    """Crea el layout mutable y copia datos legacy sin escribir junto al EXE."""
    root = data_root()
    for name in LAYOUT_DIRECTORIES:
        (root / name).mkdir(parents=True, exist_ok=True)
    secret_root().mkdir(parents=True, exist_ok=True)
    marker = root / "config" / "migration-v2.complete"
    sources = [] if marker.exists() else _legacy_sources(root)
    conflicts = []
    for source in sources:
        conflicts.extend(_copy_legacy_tree(source, root))
    if conflicts:
        joined = ", ".join(str(path) for path in conflicts[:5])
        raise ValueError(f"migración detenida por conflictos de datos legacy: {joined}")
    if not marker.exists():
        temporary = marker.with_suffix(".tmp")
        temporary.write_text("LANCTL-DATA-V2\n", encoding="ascii")
        temporary.replace(marker)
    return root.resolve()


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
        if destination.exists():
            if not _same_file(item, destination):
                conflicts.append(relative)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, destination)
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
