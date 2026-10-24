from __future__ import annotations

import json
import sqlite3
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile

from lanctl.core.config import load_config, update_config
from lanctl.core.file_transaction import atomic_write_json, locked_files
from lanctl.core.paths import application_path
from lanctl.core.projects import physical
from lanctl.core.projects.paths import resolve_project_path
from lanctl.core.projects.vlf import inspect_project, validate_project_id, verify_project


class ProjectChangesPendingError(RuntimeError):
    """Impide sobrescribir o abandonar un workspace con cambios locales."""


def project_used_elsewhere(project: str | Path) -> bool:
    """Check live sessions before discarding shared working data."""
    from lanctl.core.coordination import Coordinator
    from lanctl.core.session import current_session

    session = current_session()
    coordinator = session.coordinator if session else Coordinator()
    source = Path(project).resolve()
    return any(
        (session is None or item["id"] != session.id)
        and item.get("project")
        and Path(item["project"]).resolve() == source
        for item in coordinator.sessions()
    )


def discard_workspace_on_close(settings: Mapping[str, Any]) -> bool:
    """Return True when pending shared edits must remain for other sessions."""
    from lanctl.core.projects.save_policy import workspace_is_dirty

    project = settings.get("activeProject")
    if not project or not workspace_is_dirty(settings):
        return False
    if project_used_elsewhere(project):
        return True
    try:
        # Rechecks peers and changes under the storage locks. A session may
        # have joined since the initial check; never bypass that protection.
        root = Path(settings["projectWorkspace"]["database"]).parent.parent
        prepare_project_workspace(project, root=root, refresh=True, discard_changes=True)
    except ProjectChangesPendingError:
        if project_used_elsewhere(project):
            return True
        raise
    return False


@dataclass(frozen=True, slots=True)
class ProjectWorkspace:
    """Copia de trabajo JSON asociada a un único proyecto VLF."""

    project: Path
    project_id: str
    database: Path
    groups: Path
    metadata: Path
    content_hash: str

    @property
    def physical(self) -> Path:
        return physical.workspace_path(self.database)


def _workspace_hash(database: Path, groups: Path) -> str:
    from lanctl.core.database import DeviceDatabase
    from lanctl.core.group_database import GroupDatabase

    store = DeviceDatabase(str(database))
    from lanctl.core.projects.fingerprint import inventory_fingerprint

    logical = inventory_fingerprint(
        [device.to_dict() for device in store.load()],
        [group.to_dict() for group in GroupDatabase(str(groups), store).load()],
    )
    return physical.fingerprint(logical, database)


def _metadata(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def workspace_files_are_dirty(database: Path, groups: Path, metadata: Path) -> bool:
    """Comprueba cambios sin depender de la configuración global activa."""

    if not database.is_file():
        return False
    return _metadata(metadata).get("workspaceHash") != _workspace_hash(database, groups)


def mark_workspace_synchronized(
    workspace: Mapping[str, Any],
    *,
    project_info: Mapping[str, Any],
    workspace_hash: str | None = None,
) -> None:
    """Confirma atómicamente que el VLF verificado contiene este workspace."""

    database = Path(str(workspace.get("database", "")))
    groups = Path(str(workspace.get("groups", "")))
    metadata_value = str(workspace.get("metadata", "")).strip()
    metadata = Path(metadata_value)
    if not database.is_file() or not metadata_value:
        raise FileNotFoundError("el workspace activo no está completo")
    with locked_files((database, groups, metadata, physical.workspace_path(database))):
        current = _metadata(metadata)
        current.update(
            {
                "schemaVersion": 1,
                "project": str(Path(str(workspace.get("project", ""))).resolve()),
                "projectId": str(project_info.get("id") or workspace.get("projectId") or ""),
                "contentHash": str(project_info.get("contentHash") or ""),
                # Usa la instantánea que se verificó. Si otro proceso escribió
                # después, su hash será distinto y seguirá figurando pendiente.
                "workspaceHash": workspace_hash or _workspace_hash(database, groups),
            }
        )
        atomic_write_json(metadata, current)


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
    refresh: bool = False,
    discard_changes: bool = False,
) -> ProjectWorkspace:
    """Materializa el inventario VLF en un workspace aislado y transaccional."""

    source = Path(project).expanduser().resolve()
    verify_project(source)
    info = inspect_project(source)
    project_id = validate_project_id(info.get("id"))
    content_hash = str(info.get("contentHash") or "")
    workspaces_root = (
        Path(root).expanduser().resolve()
        if root is not None
        else application_path("data/lc/projects/workspaces")
    ).resolve()
    workspace_root = (workspaces_root / project_id).resolve()
    if not workspace_root.is_relative_to(workspaces_root):
        raise ValueError("el workspace del proyecto está fuera de la raíz permitida")
    database = workspace_root / "devices.json"
    groups = workspace_root / "groups.json"
    metadata = workspace_root / "workspace.json"
    physical_database = physical.workspace_path(database)

    current = _metadata(metadata)
    if (
        current.get("physicalSchemaVersion") == 1
        and not physical_database.is_file()
        and not (refresh and discard_changes)
    ):
        raise FileNotFoundError(
            "Falta la base física del proyecto; recupera una copia o recarga el VLF explícitamente"
        )
    synchronized = (
        database.is_file()
        and groups.is_file()
        and physical_database.is_file()
        and current.get("project") == str(source)
        and current.get("contentHash") == content_hash
    )
    dirty = workspace_files_are_dirty(database, groups, metadata)
    # Los logs y otros metadatos auxiliares también cambian contentHash. Si el
    # inventario local tiene cambios, una reapertura normal debe conservarlos;
    # solo un refresh explícito puede pedir reemplazarlos.
    must_materialize = refresh or (not synchronized and not dirty)
    if must_materialize and dirty and not discard_changes:
        raise ProjectChangesPendingError(
            f"el proyecto {source.name} contiene cambios sin guardar; "
            "guárdalos o descártalos explícitamente antes de recargar"
        )
    if must_materialize:
        devices, group_rows = _inventory_documents(source)
        with ZipFile(source) as archive:
            physical_rows = (
                physical.decode_archive(archive.read(physical.ARCHIVE_ENTRY))
                if physical.ARCHIVE_ENTRY in archive.namelist()
                else physical.empty_inventory()
            )
        workspace_root.mkdir(parents=True, exist_ok=True)
        with locked_files((database, groups, metadata, physical_database)):
            if str(inspect_project(source).get("contentHash") or "") != content_hash:
                raise ProjectChangesPendingError(
                    "el archivo de proyecto cambió durante la apertura; vuelve a intentarlo"
                )
            # Recheck inside the lock: another launcher may have edited while
            # the archive was being read. Discard must not erase its work.
            dirty = workspace_files_are_dirty(database, groups, metadata)
            if dirty:
                shared = project_used_elsewhere(source)
                if not discard_changes or shared:
                    raise ProjectChangesPendingError(
                        "no se puede reemplazar un workspace con cambios pendientes "
                        "mientras otra sesión utiliza el proyecto; guarda o cierra esa sesión"
                    )
            atomic_write_json(database, devices)
            atomic_write_json(groups, group_rows)
            atomic_write_json(physical_database, physical_rows)
            atomic_write_json(
                metadata,
                {
                    "schemaVersion": 1,
                    "project": str(source),
                    "projectId": project_id,
                    "contentHash": content_hash,
                    "workspaceHash": _workspace_hash(database, groups),
                    "physicalSchemaVersion": 1,
                },
            )

    elif not physical_database.is_file():
        # Upgrade an old workspace without replacing its unsaved logical edits.
        with ZipFile(source) as archive:
            physical_rows = (
                physical.decode_archive(archive.read(physical.ARCHIVE_ENTRY))
                if physical.ARCHIVE_ENTRY in archive.namelist()
                else physical.empty_inventory()
            )
        with locked_files((database, groups, metadata, physical_database)):
            if not physical_database.exists():
                atomic_write_json(physical_database, physical_rows)
                current = _metadata(metadata)
                if current.get("workspaceHash"):
                    current["workspaceHash"] = physical.fingerprint(
                        current["workspaceHash"], database
                    )
                current["physicalSchemaVersion"] = 1
                atomic_write_json(metadata, current)

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
    refresh: bool = False,
    discard_changes: bool = False,
) -> ProjectWorkspace:
    """Selecciona un VLF y cambia el inventario activo a su copia de trabajo."""

    from lanctl.core.config import _load_config
    from lanctl.core.project_context import project_identity

    persisted_selection = project_identity(_load_config())
    settings = dict(config or load_config())
    source = resolve_project_path(project, settings.get("projectsDirectory"))
    previous = settings.get("projectWorkspace")
    previous_project = (
        Path(str(previous.get("project", ""))).resolve()
        if isinstance(previous, Mapping) and previous.get("project")
        else None
    )
    if previous_project is not None and previous_project != source:
        previous_database = Path(str(previous.get("database", "")))
        previous_groups = Path(str(previous.get("groups", "")))
        previous_metadata = Path(str(previous.get("metadata", "")))
        if (
            workspace_files_are_dirty(previous_database, previous_groups, previous_metadata)
            and not discard_changes
        ):
            raise ProjectChangesPendingError(
                f"el proyecto {previous_project.name} contiene cambios sin guardar; "
                "guárdalos o descártalos explícitamente antes de cambiar de proyecto"
            )
    workspace = prepare_project_workspace(
        source,
        root=root,
        refresh=refresh,
        discard_changes=discard_changes,
    )

    from lanctl.core.projects.settings import project_network_overrides

    network_preferences = project_network_overrides(source)

    def select(current: dict) -> None:
        # Preparation may take time; another launcher can select a project in
        # between. Recheck under update_config's interprocess lock.
        if project_identity(_load_config()) != persisted_selection:
            raise ProjectChangesPendingError(
                "el proyecto activo cambió durante la apertura; actualiza la vista y vuelve a intentarlo"
            )
        current.update(network_preferences)
        previous = current.get("projectWorkspace")
        previous_database = str(previous.get("database", "")) if isinstance(previous, dict) else ""
        previous_groups = str(previous.get("groups", "")) if isinstance(previous, dict) else ""
        previous_physical = (
            str(previous.get("physicalDatabase", "")) if isinstance(previous, dict) else ""
        )
        if (
            not current.get("legacyPhysicalDatabase")
            and current.get("physicalDatabase")
            and str(current["physicalDatabase"]) != previous_physical
        ):
            current["legacyPhysicalDatabase"] = current["physicalDatabase"]
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
            physicalDatabase=str(workspace.physical),
            projectWorkspace={
                "project": str(workspace.project),
                "projectId": workspace.project_id,
                "database": str(workspace.database),
                "groups": str(workspace.groups),
                "physicalDatabase": str(workspace.physical),
                "metadata": str(workspace.metadata),
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
    except (OSError, ValueError, BadZipFile, sqlite3.DatabaseError) as error:
        from lanctl.core.errors import errors

        errors.from_exception(
            error,
            origin="LANCTL.Project.Workspace.Active",
            code="PROJECT.ACTIVE.UNAVAILABLE",
            level=18,
            details={"project": str(project)},
            print_output=False,
        )
        # Un proyecto movido, borrado o dañado no debe impedir que arranque la
        # GUI. Seguirá figurando como no disponible y podrá elegirse otro.
        return None
