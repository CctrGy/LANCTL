"""Explicit isolated workspace for a future shared no-project desktop session.

Preparing this workspace does not change global configuration or adopt existing
local inventory. Desktop lifetime/selection integration is a separate operation.
"""

from __future__ import annotations

import json
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

from lanctl.core.coordination import principal_id
from lanctl.core.file_transaction import atomic_write_json, locked_files
from lanctl.core.paths import application_path
from lanctl.shared.i18n import t

from . import physical
from .workspace import _workspace_hash


@dataclass(frozen=True)
class ProvisionalWorkspace:
    identifier: str
    root: Path

    def settings(self, base):
        """Return an operation context, never persist user preferences implicitly."""
        result = deepcopy(dict(base))
        database, groups = self.root / "devices.json", self.root / "groups.json"
        result.update(
            activeProject=None,
            database=str(database),
            groups=str(groups),
            networkDatabase=str(database),
            networkGroups=str(groups),
            physicalDatabase=str(physical.workspace_path(database)),
            credentials=str(self.root / "private" / "credentials"),
            log=str(self.root / "logs"),
            programLog=str(self.root / "logs"),
            databaseLog=None,
            projectWorkspace={
                "kind": "provisional",
                "provisionalId": self.identifier,
                "database": str(database),
                "groups": str(groups),
                "physicalDatabase": str(physical.workspace_path(database)),
                "metadata": str(self.root / "workspace.json"),
            },
        )
        for key, filename in (
            ("monitorDatabase", "monitor.db"),
            ("monitorRuntime", "runtime.json"),
            ("monitorIncidents", "incidents.json"),
            ("monitorLock", "monitor.lock"),
            ("monitorProfiles", "profiles.json"),
            ("monitorAssignments", "assignments.json"),
        ):
            result[key] = str(self.root / "monitor" / filename)
        return result


def prepare_provisional_workspace(*, root=None, identifier=None):
    """Create a fresh environment, or reopen its explicit UUID without resetting it."""
    reopening = identifier is not None
    identity = str(UUID(str(identifier))) if reopening else str(uuid4())
    parent = Path(root).resolve() if root is not None else application_path("data/lc/provisional")
    directory = parent / identity
    metadata = directory / "workspace.json"
    database, groups = directory / "devices.json", directory / "groups.json"
    physical_database = physical.workspace_path(database)
    paths = (database, groups, physical_database, metadata)
    if reopening and not metadata.is_file():
        raise ValueError(t("LANCTL.PROJECT.PROVISIONAL.INVALID"))
    if directory.is_symlink() or any(
        path.is_symlink() or not path.resolve().is_relative_to(directory.resolve())
        for path in paths
    ):
        raise ValueError(t("LANCTL.PROJECT.PROVISIONAL.INVALID"))
    with locked_files(paths):
        if reopening:
            document = json.loads(metadata.read_text(encoding="utf-8"))
            if (
                not isinstance(document, dict)
                or type(document.get("schemaVersion")) is not int
                or document["schemaVersion"] != 1
                or document.get("kind") != "provisional"
                or document.get("provisionalId") != identity
                or document.get("principal") != principal_id()
                or not all(path.is_file() for path in paths)
            ):
                raise ValueError(t("LANCTL.PROJECT.PROVISIONAL.INVALID"))
            # Validate all domain stores; corruption must never become empty data.
            _workspace_hash(database, groups)
        else:
            atomic_write_json(database, [])
            atomic_write_json(groups, [])
            atomic_write_json(physical_database, physical.empty_inventory())
            atomic_write_json(
                metadata,
                {
                    "schemaVersion": 1,
                    "kind": "provisional",
                    "provisionalId": identity,
                    "principal": principal_id(),
                    "physicalSchemaVersion": 1,
                    "workspaceHash": _workspace_hash(database, groups),
                },
            )
    return ProvisionalWorkspace(identity, directory)


def save_provisional_project(workspace, destination, *, name, base):
    """Save and verify a consistent VLF; keep the source for cancellation/retry.

    Promotion/selection and the final close decision belong to the shared owner.
    Credentials and operational logs never enter this provisional save route.
    """
    from .vlf import create_project, verify_project
    from .workspace import prepare_project_workspace

    current = prepare_provisional_workspace(
        root=workspace.root.parent, identifier=workspace.identifier
    )
    settings = current.settings(base)
    database, groups = Path(settings["database"]), Path(settings["groups"])
    destination = Path(destination).expanduser().resolve()
    paths = (
        database,
        groups,
        physical.workspace_path(database),
        current.root / "workspace.json",
        destination,
    )
    with (
        locked_files(paths),
        tempfile.TemporaryDirectory(prefix="lanctl-provisional-save-") as temporary,
    ):
        expected = _workspace_hash(database, groups)
        settings.update(
            credentials=str(Path(temporary) / "no-credentials"),
            databaseLog=None,
            log=str(Path(temporary) / "no-logs"),
            programLog=str(Path(temporary) / "no-logs"),
        )
        result = create_project(destination, name=name, config=settings, initialize_reserved=False)
        verification = verify_project(result["path"])
        reopened = prepare_project_workspace(result["path"], root=Path(temporary) / "verification")
        if _workspace_hash(reopened.database, reopened.groups) != expected:
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.SAVE_MISMATCH"))
    return {**result, "verified": verification, "workspaceHash": expected}


@contextmanager
def _owner_state(workspace, session_id, coordinator):
    """Only registered sessions of the current OS principal may own this state."""
    metadata = workspace.root / "workspace.json"
    with locked_files((metadata,)):
        live = {row["id"] for row in coordinator.sessions()}
        if session_id not in live:
            raise ValueError(t("LANCTL.PROJECT.PROVISIONAL.INVALID"))
        document = json.loads(metadata.read_text(encoding="utf-8"))
        if (
            not isinstance(document, dict)
            or type(document.get("schemaVersion")) is not int
            or document["schemaVersion"] != 1
            or document.get("kind") != "provisional"
            or document.get("provisionalId") != workspace.identifier
            or document.get("principal") != coordinator.owner
            or not isinstance(document.get("owners", []), list)
            or any(not isinstance(owner, str) for owner in document.get("owners", []))
            or type(document.get("closed", False)) is not bool
            or not isinstance(document.get("closeLease", {}), dict)
        ):
            raise ValueError(t("LANCTL.PROJECT.PROVISIONAL.INVALID"))
        document["owners"] = sorted(set(document.get("owners", [])) & live)
        if document.get("closeLease", {}).get("owner") not in live:
            document.pop("closeLease", None)
        yield document
        atomic_write_json(metadata, document)


def join_provisional_workspace(workspace, session_id, *, coordinator):
    with _owner_state(workspace, session_id, coordinator) as document:
        if document.get("closeLease") or document.get("closed"):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        document["owners"] = sorted(set(document["owners"]) | {session_id})


def claim_provisional_close(workspace, session_id, *, coordinator):
    """Serialize close requests; retain the owner until its native close succeeds."""
    from .save_policy import workspace_is_dirty

    with _owner_state(workspace, session_id, coordinator) as document:
        if (
            session_id not in document["owners"]
            or document.get("closeLease")
            or document.get("closed")
        ):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        token = str(uuid4())
        last = len(document["owners"]) == 1
        document["closeLease"] = {"owner": session_id, "token": token}
        return {"token": token, "last": last, "dirty": workspace_is_dirty(workspace.settings({}))}


def cancel_provisional_close(workspace, session_id, token, *, coordinator):
    with _owner_state(workspace, session_id, coordinator) as document:
        lease = document.get("closeLease", {})
        if not _matches_lease(lease, session_id, token) or lease.get("saving"):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        document.pop("closeLease")


def _matches_lease(lease, session_id, token):
    return lease.get("owner") == session_id and lease.get("token") == token


def prepare_provisional_close(
    workspace,
    session_id,
    token,
    *,
    coordinator,
    decision="ask",
    destination=None,
    name="",
    base=None,
):
    """Resolve the decision before native close; a failed close can still cancel."""
    from .save_policy import workspace_is_dirty

    with _owner_state(workspace, session_id, coordinator) as document:
        lease = document.get("closeLease", {})
        if not _matches_lease(lease, session_id, token) or lease.get("saving"):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        if decision == "cancel":
            document.pop("closeLease")
            return {"ready": False, "cancelled": True}
        last = len(document["owners"]) == 1
        dirty = workspace_is_dirty(workspace.settings({}))
        if not last or not dirty:
            lease["resolution"] = "retain" if not last else "unchanged"
            return {"ready": True, "last": last}
        if decision == "discard":
            lease["resolution"] = "discard"
            return {"ready": True, "last": True}
        if decision != "save" or not destination:
            return {"ready": False, "last": True, "needsDecision": True}
        lease["saving"] = True
    # Never acquire the full storage lock set while retaining the metadata lock.
    try:
        result = save_provisional_project(workspace, destination, name=name, base=base or {})
    except BaseException:
        with _owner_state(workspace, session_id, coordinator) as document:
            lease = document.get("closeLease", {})
            if _matches_lease(lease, session_id, token):
                lease.pop("saving", None)
        raise
    with _owner_state(workspace, session_id, coordinator) as document:
        lease = document.get("closeLease", {})
        if not _matches_lease(lease, session_id, token):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        lease.pop("saving", None)
        lease.update(
            resolution="save", savedHash=result["workspaceHash"], savedProject=result["path"]
        )
    return {"ready": True, "last": True, "project": result["path"]}


def complete_provisional_close(workspace, session_id, token, *, coordinator):
    """Acknowledge successful native close; retain source files for recovery."""
    from .save_policy import workspace_is_dirty

    with _owner_state(workspace, session_id, coordinator) as document:
        lease = document.get("closeLease", {})
        if not _matches_lease(lease, session_id, token) or lease.get("saving"):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        last = len(document["owners"]) == 1
        if last and workspace_is_dirty(workspace.settings({})):
            database, groups = workspace.root / "devices.json", workspace.root / "groups.json"
            saved = lease.get("resolution") == "save" and lease.get("savedHash") == _workspace_hash(
                database, groups
            )
            if lease.get("resolution") != "discard" and not saved:
                raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        elif not lease.get("resolution"):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        document["owners"].remove(session_id)
        document.pop("closeLease")
        if not document["owners"]:
            document["closed"] = True
        return {"closed": True, "last": last}


@contextmanager
def provisional_operation(workspace, session_id, *, coordinator, base):
    """Cooperating writes cannot pass a pending close decision."""
    with _owner_state(workspace, session_id, coordinator) as document:
        if (
            session_id not in document["owners"]
            or document.get("closeLease")
            or document.get("closed")
        ):
            raise RuntimeError(t("LANCTL.PROJECT.PROVISIONAL.BUSY"))
        yield workspace.settings(base)
