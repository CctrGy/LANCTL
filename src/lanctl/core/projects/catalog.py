from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from lanctl.core.file_transaction import locked_file
from lanctl.core.paths import application_path

CATALOG_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class ProjectCatalogEntry:
    path: Path
    name: str
    project_id: str = ""
    in_default_directory: bool = False
    available: bool = True
    discovered_at: str = ""
    last_seen: str = ""


def default_catalog_path() -> Path:
    return application_path("data/lc/projects/projects.db")


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path.expanduser().resolve()))


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


class ProjectCatalog:
    """Catálogo persistente de proyectos VLF conocidos por LANCTL."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else default_catalog_path()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                path_key TEXT PRIMARY KEY,
                path TEXT NOT NULL,
                name TEXT NOT NULL,
                project_id TEXT NOT NULL DEFAULT '',
                discovered_at TEXT NOT NULL,
                last_seen TEXT NOT NULL
            )
            """
        )
        connection.execute(f"PRAGMA user_version = {CATALOG_SCHEMA_VERSION}")
        connection.commit()
        return connection

    def register(self, path: str | Path) -> None:
        project = Path(path).expanduser().resolve()
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        name = project.stem
        project_id = ""
        if project.is_file():
            try:
                from lanctl.core.projects.vlf import inspect_project

                info = inspect_project(project)
                name = str(info.get("name") or name)
                project_id = str(info.get("id") or "")
            except (OSError, ValueError, sqlite3.DatabaseError):
                pass
        with locked_file(self.path), closing(self._connect()) as connection:
            connection.execute(
                """
                    INSERT INTO projects(path_key, path, name, project_id, discovered_at, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(path_key) DO UPDATE SET
                        path=excluded.path,
                        name=excluded.name,
                        project_id=CASE WHEN excluded.project_id = ''
                            THEN projects.project_id ELSE excluded.project_id END,
                        last_seen=excluded.last_seen
                    """,
                (_path_key(project), str(project), name, project_id, now, now),
            )
            connection.commit()

    def refresh(
        self, default_root: str | Path, *, active_path: str | Path | None = None
    ) -> list[ProjectCatalogEntry]:
        root = Path(default_root).expanduser().resolve()
        if root.exists():
            for project in root.rglob("*.vlf"):
                if project.is_file():
                    self.register(project)
        if active_path:
            self.register(active_path)
        return self.list(root)

    def list(self, default_root: str | Path) -> list[ProjectCatalogEntry]:
        root = Path(default_root).expanduser().resolve()
        with locked_file(self.path), closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT path, name, project_id, discovered_at, last_seen FROM projects"
            ).fetchall()
        entries = [
            ProjectCatalogEntry(
                path=Path(row["path"]),
                name=row["name"],
                project_id=row["project_id"],
                in_default_directory=_inside(Path(row["path"]), root),
                available=Path(row["path"]).is_file(),
                discovered_at=row["discovered_at"],
                last_seen=row["last_seen"],
            )
            for row in rows
        ]
        return sorted(
            entries,
            key=lambda item: (
                not item.in_default_directory,
                item.name.casefold(),
                str(item.path).casefold(),
            ),
        )

    def remove(self, path: str | Path, *, delete_file: bool = False) -> None:
        project = Path(path).expanduser().resolve()
        if delete_file and project.exists():
            with locked_file(project):
                project.unlink()
        with locked_file(self.path), closing(self._connect()) as connection:
            connection.execute("DELETE FROM projects WHERE path_key = ?", (_path_key(project),))
            connection.commit()
