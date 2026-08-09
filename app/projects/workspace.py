from __future__ import annotations

import json
import sqlite3
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from app.core.config import load_config, update_config
from app.core.file_transaction import atomic_write_json, locked_files
from app.core.paths import application_path
from app.projects.paths import resolve_project_path
from app.projects.vlf import inspect_project, verify_project


@dataclass(frozen=True, slots=True)
class ProjectWorkspace:
    """Copia de trabajo JSON asociada a un único proyecto VLF."""

    project: Path
    project_id: str
    database: Path
    groups: Path
    metadata: Path
    content_hash: str


def _inventory_documents(project: Path) -> tuple[list[dict], list[dict]]:
    """Lee el SQLite del VLF sin extraer rutas arbitrarias del archivo ZIP."""

    with ZipFile(project, "r") as archive:
        database_bytes = archive.read("devices/elements.db")

    with tempfile.TemporaryDirectory(prefix="lanctl-project-workspace-") as temporary:
        database_path = Path(temporary) / "elements.db"
        database_path.write_bytes(database_bytes)
        connection = sqlite3.connect(f"file:{database_path.as_posix()}?mode=ro", uri=True)
        try:
            devices = []
            device_macs: dict[str, str] = {}
            for device_id, mac, raw_json in connection.execute(
                "SELECT device_id, mac, raw_json FROM devices ORDER BY rowid"
            ):
                payload = json.loads(raw_json)
                if not isinstance(payload, dict):
                    raise ValueError("raw_json de dispositivo VLF no es un objeto")
                devices.append(payload)
                if mac:
                    device_macs[str(device_id)] = str(mac)

            members: dict[str, list[str]] = {}
            for group_name, device_id in connection.execute(
                "SELECT group_name, device_id FROM group_members ORDER BY group_name, device_id"
            ):
                mac = device_macs.get(str(device_id))
                if mac:
                    members.setdefault(str(group_name), []).append(mac)

            groups = [
                {
                    "name": str(name),
                    "description": str(description or ""),
                    "members": members.get(str(name), []),
                    "editable": bool(editable),
                }
                for name, description, editable in connection.execute(
                    "SELECT name, description, editable FROM groups ORDER BY rowid"
                )
            ]
        finally:
            connection.close()
    return devices, groups


def prepare_project_workspace(
    project: str | Path,
    *,
    root: str | Path | None = None,
    refresh: bool = True,
) -> ProjectWorkspace:
    """Materializa el inventario VLF en un workspace aislado y transaccional."""

    source = Path(project).expanduser().resolve()
    verify_project(source)
    info = inspect_project(source)
    project_id = str(info.get("id") or "").strip()
    if not project_id:
        raise ValueError("el proyecto VLF no contiene UUID")
    content_hash = str(info.get("contentHash") or "")
    workspace_root = (
        Path(root).expanduser().resolve()
        if root is not None
        else application_path("data/lc/projects/workspaces")
    ) / project_id
    database = workspace_root / "devices.json"
    groups = workspace_root / "groups.json"
    metadata = workspace_root / "workspace.json"

    current: dict[str, Any] = {}
    if metadata.is_file():
        try:
            value = json.loads(metadata.read_text(encoding="utf-8"))
            current = value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            current = {}
    synchronized = (
        database.is_file()
        and groups.is_file()
        and current.get("project") == str(source)
        and current.get("contentHash") == content_hash
    )
    if refresh or not synchronized:
        devices, group_rows = _inventory_documents(source)
        workspace_root.mkdir(parents=True, exist_ok=True)
        with locked_files((database, groups, metadata)):
            atomic_write_json(database, devices)
            atomic_write_json(groups, group_rows)
            atomic_write_json(
                metadata,
                {
                    "schemaVersion": 1,
                    "project": str(source),
                    "projectId": project_id,
                    "contentHash": content_hash,
                },
            )

    return ProjectWorkspace(
        project=source,
        project_id=project_id,
        database=database,
        groups=groups,
        metadata=metadata,
        content_hash=content_hash,
    )


def activate_project_workspace(
    project: str | Path,
    *,
    config: Mapping[str, Any] | None = None,
    root: str | Path | None = None,
    refresh: bool = True,
) -> ProjectWorkspace:
    """Selecciona un VLF y cambia el inventario activo a su copia de trabajo."""

    settings = dict(config or load_config())
    source = resolve_project_path(project, settings.get("projectsDirectory"))
    workspace = prepare_project_workspace(source, root=root, refresh=refresh)

    def select(current: dict) -> None:
        previous = current.get("projectWorkspace")
        previous_database = str(previous.get("database", "")) if isinstance(previous, dict) else ""
        previous_groups = str(previous.get("groups", "")) if isinstance(previous, dict) else ""
        if (
            not current.get("networkDatabase")
            and str(current.get("database", "")) != previous_database
        ):
            current["networkDatabase"] = current.get("database")
        if not current.get("networkGroups") and str(current.get("groups", "")) != previous_groups:
            current["networkGroups"] = current.get("groups")
        current.update(
            activeProject=str(workspace.project),
            database=str(workspace.database),
            groups=str(workspace.groups),
            projectWorkspace={
                "project": str(workspace.project),
                "projectId": workspace.project_id,
                "database": str(workspace.database),
                "groups": str(workspace.groups),
                "contentHash": workspace.content_hash,
            },
        )
        current.pop("databaseLog", None)

    update_config(select)
    return workspace


def ensure_active_project_workspace() -> ProjectWorkspace | None:
    """Repara configuraciones antiguas que solo guardaban ``activeProject``."""

    settings = load_config()
    project = settings.get("activeProject")
    if not project:
        return None
    try:
        return activate_project_workspace(project, config=settings, refresh=False)
    except (OSError, ValueError, BadZipFile, sqlite3.DatabaseError):
        # Un proyecto movido, borrado o dañado no debe impedir que arranque la
        # GUI. Seguirá figurando como no disponible y podrá elegirse otro.
        return None
