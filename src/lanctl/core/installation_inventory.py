"""Owned-file inventory and read-only cleanup planning; never deletes resources."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lanctl.core.file_transaction import (
    atomic_write_text,
    locked_file,
    locked_files,
)
from lanctl.shared.i18n import t

MAX_INVENTORY_BYTES = 1024 * 1024
MAX_INVENTORY_FILES = 4096


def _plain_path(path):
    path = Path(path)
    if (
        not path.is_absolute()
        or ".." in path.parts
        or any(item.is_symlink() or item.is_junction() for item in (path, *path.parents))
    ):
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.UNSAFE_PATH"))
    return path


def _digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _load(manifest):
    if not manifest.exists():
        return {"schemaVersion": 1, "files": []}
    with manifest.open("rb") as stream:
        raw = stream.read(MAX_INVENTORY_BYTES + 1)
    if len(raw) > MAX_INVENTORY_BYTES:
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.INVALID"))
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.INVALID")) from error
    _validate(value)
    return value


def _validate(value):
    if (
        not isinstance(value, dict)
        or set(value) != {"schemaVersion", "files"}
        or type(value.get("schemaVersion")) is not int
        or value["schemaVersion"] != 1
        or not isinstance(value.get("files"), list)
        or len(value["files"]) > MAX_INVENTORY_FILES
        or any(
            not isinstance(item, dict)
            or set(item) != {"root", "relative", "sha256"}
            or any(not isinstance(field, str) for field in item.values())
            or len(item["sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in item["sha256"])
            for item in value["files"]
        )
    ):
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.INVALID"))
    identities = [(item["root"], item["relative"]) for item in value["files"]]
    if len(set(identities)) != len(identities):
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.INVALID"))


def _encode(value):
    _validate(value)
    payload = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    try:
        size = len(payload.encode("utf-8"))
    except UnicodeError as error:
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.INVALID")) from error
    if size > MAX_INVENTORY_BYTES:
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.INVALID"))
    return payload


def record_installed_file(manifest, root, path):
    """Call after writing an installer-owned file; do not infer ownership by name."""
    manifest, root, path = map(_plain_path, (manifest, root, path))
    if path == root or not path.is_relative_to(root) or not path.is_file():
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.UNSAFE_PATH"))
    entry = {
        "root": str(root),
        "relative": path.relative_to(root).as_posix(),
        "sha256": _digest(path),
    }
    with locked_file(manifest):
        document = _load(manifest)
        document["files"] = [
            item
            for item in document["files"]
            if (item["root"], item["relative"]) != (entry["root"], entry["relative"])
        ] + [entry]
        atomic_write_text(manifest, _encode(document))


def plan_owned_file_cleanup(manifest, *, allowed_roots):
    """Re-resolve trusted roots outside the manifest; preserve changed/unsafe files."""
    manifest = _plain_path(manifest)
    roots = {_plain_path(root) for root in allowed_roots}
    result = {"removable": [], "preserved": [], "missing": [], "unsafe": []}
    with locked_file(manifest):
        document = _load(manifest)
        for entry in document["files"]:
            relative = Path(entry["relative"])
            root = Path(entry["root"])
            if (
                root not in roots
                or relative.is_absolute()
                or not relative.parts
                or ".." in relative.parts
            ):
                result["unsafe"].append(dict(entry))
                continue
            path = root / relative
            try:
                _plain_path(path)
            except ValueError:
                result["unsafe"].append(dict(entry))
                continue
            if not path.exists():
                result["missing"].append(str(path))
            elif path.is_file() and _digest(path) == entry["sha256"]:
                result["removable"].append(str(path))
            else:
                result["preserved"].append(str(path))
    return result


def write_installed_file(manifest, root, path, content):
    """Preserve unrelated/edited files instead of adopting them during upgrade."""
    manifest, root, path = map(_plain_path, (manifest, root, path))
    if path == root or not path.is_relative_to(root):
        raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.UNSAFE_PATH"))
    relative = path.relative_to(root).as_posix()
    with locked_files((manifest, path)):
        document = _load(manifest)
        previous = next(
            (
                item
                for item in document["files"]
                if item["root"] == str(root) and item["relative"] == relative
            ),
            None,
        )
        if path.exists():
            current = _digest(path) if path.is_file() else None
            expected = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if current is None or (
                current != expected and (previous is None or current != previous["sha256"])
            ):
                raise ValueError(t("LANCTL.INSTALLATION.INVENTORY.CONFLICT"))
        entry = {
            "root": str(root),
            "relative": relative,
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        }
        document["files"] = [
            item
            for item in document["files"]
            if (item["root"], item["relative"]) != (str(root), relative)
        ] + [entry]
        payload = _encode(document)
        atomic_write_text(path, content)
        atomic_write_text(manifest, payload)
