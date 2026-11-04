"""Durable rollback for multi-store imports and recovery at store boundaries."""

from __future__ import annotations

import base64
import hashlib
import json
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

from lanctl.core import file_transaction as ft
from lanctl.shared.i18n import t

JOURNAL_NAME = ".lanctl-import.transaction"
MARKER_SUFFIX = ".lanctl-import.pending"
_STATE = threading.local()


@contextmanager
def _guard():
    previous = getattr(_STATE, "active", False)
    _STATE.active = True
    try:
        yield
    finally:
        _STATE.active = previous


def marker_path(path: str | Path) -> Path:
    target = Path(path)
    return target.with_name(target.name + MARKER_SUFFIX)


def pending(paths) -> bool:
    if getattr(_STATE, "active", False):
        return False
    return any(marker_path(path).exists() or marker_path(path).is_symlink() for path in paths)


class ImportRecoveryError(ValueError):
    """A store must remain unavailable until pending recovery is repaired."""


def _invalid():
    return ImportRecoveryError(t("LANCTL.STORAGE.ERROR.IMPORT_JOURNAL"))


def _snapshot(payload: bytes | None) -> dict:
    return {
        "exists": payload is not None,
        "data": base64.b64encode(payload).decode("ascii") if payload is not None else "",
        "sha256": hashlib.sha256(payload).hexdigest() if payload is not None else "",
    }


def _decode(snapshot) -> bytes | None:
    if not isinstance(snapshot, dict) or type(snapshot.get("exists")) is not bool:
        raise _invalid()
    if not snapshot["exists"]:
        if snapshot.get("data") != "" or snapshot.get("sha256") != "":
            raise _invalid()
        return None
    try:
        payload = base64.b64decode(snapshot["data"], validate=True)
    except (ValueError, TypeError, KeyError) as error:
        raise _invalid() from error
    if hashlib.sha256(payload).hexdigest() != snapshot.get("sha256"):
        raise _invalid()
    return payload


def _read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise _invalid()
    try:
        value = json.loads(path.read_bytes())
    except (ValueError, UnicodeError) as error:
        raise _invalid() from error
    if not isinstance(value, dict):
        raise _invalid()
    return value


def _pointer(journal, document, target):
    return {
        "schemaVersion": 1,
        "transactionId": document["transactionId"],
        "journal": str(journal),
        "target": str(target),
    }


def _read_journal(journal: Path, *, check_markers=True):
    document = _read_json(journal)
    if (
        type(document.get("schemaVersion")) is not int
        or document["schemaVersion"] != 1
        or document.get("phase") not in {"prepared", "committed", "rolled-back"}
        or not isinstance(document.get("transactionId"), str)
        or len(document["transactionId"]) != 32
        or document.get("root") != str(journal.parent.resolve())
        or journal.name != JOURNAL_NAME
        or journal != journal.resolve()
        or not isinstance(document.get("entries"), list)
        or not document["entries"]
    ):
        raise _invalid()
    entries = {}
    for entry in document["entries"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise _invalid()
        target = Path(entry["path"])
        if (
            not target.is_absolute()
            or target != target.resolve()
            or target in entries
            or target.name == JOURNAL_NAME
            or target.name.endswith(MARKER_SUFFIX)
            or not isinstance(entry.get("afterSha256"), str)
            or len(entry["afterSha256"]) != 64
        ):
            raise _invalid()
        before = _decode(entry.get("before"))
        marker = marker_path(target)
        if not check_markers:
            entries[target] = before
            continue
        if marker.exists() or marker.is_symlink():
            if _read_json(marker) != _pointer(journal, document, target):
                raise _invalid()
        elif document["phase"] == "prepared":
            # No data is written until every marker is durable. A missing marker
            # in this phase is valid only while its original state is untouched.
            current = target.read_bytes() if target.is_file() else None
            if current != before or (target.exists() and not target.is_file()):
                raise _invalid()
        entries[target] = before
    return document, entries


def _cleanup(journal, document, entries):
    for target in entries:
        marker = marker_path(target)
        if marker.exists() or marker.is_symlink():
            if _read_json(marker) != _pointer(journal, document, target):
                raise _invalid()
            marker.unlink()
            ft.fsync_directory(marker.parent)
    journal.unlink()
    ft.fsync_directory(journal.parent)


def recover_journal(journal: str | Path, *, requested=()) -> bool:
    journal = Path(journal)
    with _guard():
        try:
            while journal.exists() or journal.is_symlink():
                try:
                    initial, entries = _read_journal(journal, check_markers=False)
                except (ValueError, FileNotFoundError):
                    if not journal.exists() and not journal.is_symlink():
                        return False
                    raise
                if not set(requested).issubset(entries):
                    if all(not marker_path(path).exists() for path in requested):
                        return False
                    raise _invalid()
                with ft.locked_files((journal, *entries)):
                    if not journal.exists():
                        return False
                    document, observed = _read_journal(journal)
                    if document["transactionId"] != initial["transactionId"] or entries != observed:
                        # Another transaction won the root lock. Release all old
                        # destination locks before discovering the current set.
                        continue
                    if not set(requested).issubset(observed):
                        raise _invalid()
                    if document["phase"] == "prepared":
                        for target, before in observed.items():
                            if not marker_path(target).exists():
                                continue
                            if before is None:
                                target.unlink(missing_ok=True)
                                ft.fsync_directory(target.parent)
                            else:
                                ft.atomic_write_bytes(target, before)
                        document["phase"] = "rolled-back"
                        ft.atomic_write_json(journal, document)
                    _cleanup(journal, document, observed)
                    return True
            return False
        except Exception as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.Storage.Import.Recovery",
                code="STORAGE.IMPORT.RECOVERY_FAILED",
                level=43,
                print_output=False,
            )
            raise


def recover_for_paths(paths) -> None:
    paths = tuple(paths)
    if not pending(paths):
        return
    journals = {}
    for path in paths:
        target = Path(path).resolve()
        marker = marker_path(target)
        if not marker.exists() and not marker.is_symlink():
            continue
        try:
            value = _read_json(marker)
        except (ValueError, FileNotFoundError):
            if not marker.exists() and not marker.is_symlink():
                continue
            raise
        if (
            type(value.get("schemaVersion")) is not int
            or value["schemaVersion"] != 1
            or value.get("target") != str(target)
            or not isinstance(value.get("journal"), str)
        ):
            raise _invalid()
        journal = Path(value["journal"])
        if (
            not journal.is_absolute()
            or journal.name != JOURNAL_NAME
            or journal != journal.resolve()
        ):
            raise _invalid()
        if not journal.exists():
            if not marker.exists():
                continue
            raise _invalid()
        journals.setdefault(journal, set()).add(target)
    for journal, requested in sorted(journals.items()):
        recover_journal(journal, requested=requested)


def _durable_directory(path: Path) -> None:
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    path.mkdir(parents=True, exist_ok=True)
    for created in reversed(missing):
        ft.fsync_directory(created.parent)


def commit_import(root: Path, targets, payloads, *, prepare=None, companions=()) -> None:
    """Publish all new bytes or roll back; interrupted commits recover on read."""
    journal = root / JOURNAL_NAME
    for directory in {root, *(target.parent for target in targets)}:
        _durable_directory(directory)
    recover_journal(journal)
    with ft.locked_files((journal, *targets, *companions)), _guard():
        if journal.exists() or any(marker_path(target).exists() for target in targets):
            raise _invalid()
        if any(
            target.name == JOURNAL_NAME or target.name.endswith(MARKER_SUFFIX) for target in targets
        ):
            raise _invalid()
        if prepare:
            prepare()
        originals = {
            target: target.read_bytes() if target.is_file() else None for target in targets
        }
        if any(target.exists() and not target.is_file() for target in targets):
            raise _invalid()
        document = {
            "schemaVersion": 1,
            "transactionId": uuid.uuid4().hex,
            "root": str(root),
            "phase": "prepared",
            "entries": [
                {
                    "path": str(target),
                    "before": _snapshot(originals[target]),
                    "afterSha256": hashlib.sha256(payload).hexdigest(),
                }
                for target, payload in zip(targets, payloads)
            ],
        }
        ft.atomic_write_json(journal, document)
        try:
            for target in targets:
                ft.atomic_write_json(marker_path(target), _pointer(journal, document, target))
            for target, payload in zip(targets, payloads):
                ft.atomic_write_bytes(target, payload)
            document["phase"] = "committed"
            ft.atomic_write_json(journal, document)
        except Exception:
            # Recovery keeps journal/markers if restoring any file fails.
            recover_journal(journal)
            raise
        _cleanup(journal, document, originals)
