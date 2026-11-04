from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
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
    validation: str = "not-checked"


def create_backup(path: str | Path, *, directory: str | Path | None = None) -> Path:
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    target_root = Path(directory) if directory else source.parent / "backups"
    target_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    descriptor, name = tempfile.mkstemp(
        prefix=f"{source.name}.{timestamp}.", suffix=".bak", dir=target_root
    )
    os.close(descriptor)
    target = Path(name)
    try:
        with locked_files((source, target)):
            shutil.copy2(source, target)
            with target.open("rb") as snapshot:
                os.fsync(snapshot.fileno())
            from lanctl.core.file_transaction import fsync_directory

            fsync_directory(target_root)
            fsync_directory(target_root.parent)
    except Exception:
        target.unlink(missing_ok=True)
        raise
    return target


def _contracts(values: dict[str | Path, str] | None) -> dict[Path, str]:
    if values is None:
        from lanctl.core.storage_validation import configured_contracts

        return configured_contracts()
    return {Path(path).resolve(): contract for path, contract in values.items()}


def _validate_payload(path: Path, payload: bytes, contract: str | None) -> tuple[str, str]:
    if contract or path.suffix.casefold() in {".json", ".registry"} or path.name == ".config":
        value = json.loads(payload.decode("utf-8"))
        if contract:
            from lanctl.core.storage_validation import validate_document

            validate_document(value, contract, path=path)
            return "json", "functional"
        return "json", "syntax-only"
    return ("sqlite" if payload.startswith(b"SQLite format 3\x00") else "binary"), "not-checked"


def restore_backup(path: str | Path, backup: str | Path, *, contract: str | None = None) -> Path:
    target, source = Path(path), Path(backup)
    if contract is None:
        contract = _contracts(None).get(target.resolve())
    with locked_files((target, source)):
        from lanctl.core.file_transaction import atomic_write_bytes

        # Validate and write exactly one protected snapshot, not two reads.
        payload = source.read_bytes()
        _validate_payload(target, payload, contract)
        atomic_write_bytes(target, payload)
    return target


def diagnose_storage(
    paths: list[str | Path], *, contracts: dict[str | Path, str] | None = None
) -> list[StorageCheck]:
    from lanctl.shared.i18n import t

    known = _contracts(contracts)
    checks: list[StorageCheck] = []
    resolved: set[str] = set()
    for value in paths:
        path = Path(value).resolve()
        key = os.path.normcase(str(path))
        if key in resolved:
            continue
        resolved.add(key)
        try:
            with locked_files((path,)):
                if not path.exists():
                    checks.append(
                        StorageCheck(
                            str(path),
                            False,
                            False,
                            "missing",
                            t("LANCTL.STORAGE.DIAGNOSIS.MISSING"),
                        )
                    )
                    continue
                if not path.is_file():
                    checks.append(
                        StorageCheck(
                            str(path),
                            True,
                            False,
                            "unsupported",
                            t("LANCTL.STORAGE.DIAGNOSIS.NOT_FILE"),
                        )
                    )
                    continue
                payload = path.read_bytes()
                kind, validation = _validate_payload(path, payload, known.get(path))
            detail = hashlib.sha256(payload).hexdigest()
            if validation == "syntax-only":
                detail = t("LANCTL.STORAGE.DIAGNOSIS.SYNTAX_ONLY") + "; sha256=" + detail
            checks.append(StorageCheck(str(path), True, True, kind, detail, validation))
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
            checks.append(
                StorageCheck(str(path), path.exists(), False, "corrupt", str(error), "failed")
            )
    return checks


def export_storage(
    paths: list[str | Path],
    destination: str | Path,
    *,
    source_root: str | Path | None = None,
    destinations: dict[str, str | Path] | None = None,
) -> Path:
    target = Path(destination)
    from lanctl.shared.i18n import t

    if source_root is not None and destinations is not None:
        raise ValueError(t("LANCTL.STORAGE.ERROR.EXPORT_LAYOUT"))
    if destinations is not None:
        entries = {name: Path(path).resolve() for name, path in destinations.items()}
        for name in entries:
            if name not in {"devices", "groups", "physical", "config", "plugins"}:
                raise ValueError(t("LANCTL.STORAGE.ERROR.CONTRACT", contract=name))
        entries = {name: path for name, path in entries.items() if path.is_file()}
        layout = "logical"
    else:
        files = [Path(path).resolve() for path in paths if Path(path).is_file()]
        if not files:
            raise ValueError(t("LANCTL.STORAGE.ERROR.NO_FILES"))
        common = (
            Path(source_root).resolve()
            if source_root is not None
            else Path(os.path.commonpath([str(path.parent) for path in files]))
        )
        if any(not path.is_relative_to(common) for path in files):
            raise ValueError(t("LANCTL.STORAGE.ERROR.OUTSIDE_ROOT"))
        entries = {path.relative_to(common).as_posix(): path for path in files}
        layout = "relative"
    if not entries:
        raise ValueError(t("LANCTL.STORAGE.ERROR.NO_FILES"))
    files = list(entries.values())
    if (
        len({os.path.normcase(str(path)) for path in files}) != len(files)
        or target.resolve() in files
    ):
        raise ValueError(t("LANCTL.STORAGE.ERROR.DUPLICATE_TARGET"))
    manifest: dict[str, Any] = {
        "schemaVersion": 2 if source_root is not None or destinations is not None else 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "files": {},
    }
    if manifest["schemaVersion"] == 2:
        manifest["layout"] = layout
    target.parent.mkdir(parents=True, exist_ok=True)
    with locked_files(tuple([*files, target])):
        with tempfile.NamedTemporaryFile(delete=False, dir=target.parent, suffix=".tmp") as stream:
            temporary = Path(stream.name)
        try:
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for name, path in entries.items():
                    payload = path.read_bytes()
                    archive.writestr(f"data/{name}", payload)
                    manifest["files"][name] = hashlib.sha256(payload).hexdigest()
                archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    verify_export(target)
    return target


def _export_manifest(archive: zipfile.ZipFile) -> dict[str, Any]:
    from lanctl.shared.i18n import t

    if archive.namelist().count("manifest.json") != 1:
        raise ValueError(t("LANCTL.STORAGE.ERROR.EXPORT_MANIFEST"))
    manifest = json.loads(archive.read("manifest.json"))
    if (
        not isinstance(manifest, dict)
        or type(manifest.get("schemaVersion")) is not int
        or manifest["schemaVersion"] not in (1, 2)
    ):
        raise ValueError(t("LANCTL.STORAGE.ERROR.EXPORT_MANIFEST"))
    if manifest["schemaVersion"] == 2 and manifest.get("layout") not in ("relative", "logical"):
        raise ValueError(t("LANCTL.STORAGE.ERROR.EXPORT_MANIFEST"))
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ValueError(t("LANCTL.STORAGE.ERROR.EXPORT_MANIFEST"))
    for name, checksum in files.items():
        if (
            not isinstance(name, str)
            or not name
            or not Path(name).parts
            or ":" in name
            or "\x00" in name
            or "\\" in name
            or Path(name).is_absolute()
            or PureWindowsPath(name).drive
            or ".." in Path(name).parts
            or Path(name).as_posix() != name
        ):
            raise ValueError(t("LANCTL.STORAGE.ERROR.UNSAFE_PATH", path=name))
        if (
            not isinstance(checksum, str)
            or len(checksum) != 64
            or any(char not in "0123456789abcdef" for char in checksum)
        ):
            raise ValueError(t("LANCTL.STORAGE.ERROR.EXPORT_MANIFEST"))
        if manifest.get("layout") == "logical" and name not in {
            "devices",
            "groups",
            "physical",
            "config",
            "plugins",
        }:
            raise ValueError(t("LANCTL.STORAGE.ERROR.CONTRACT", contract=name))
        if archive.namelist().count(f"data/{name}") != 1:
            raise ValueError(t("LANCTL.STORAGE.ERROR.EXPORT_MANIFEST"))
    return manifest


def verify_export(path: str | Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        manifest = _export_manifest(archive)
        for name, expected in manifest["files"].items():
            actual = hashlib.sha256(archive.read(f"data/{name}")).hexdigest()
            if actual != expected:
                raise ValueError(f"hash incorrecto en la exportación: {name}")
    return manifest


def import_storage(
    path: str | Path,
    destination_root: str | Path,
    *,
    contracts: dict[str | Path, str] | None = None,
    destinations: dict[str, str | Path] | None = None,
) -> list[Path]:
    """Importa una exportación validada con rollback de todos los destinos."""

    known = _contracts(contracts)
    source = Path(path)
    root = Path(destination_root).resolve()
    manifest = verify_export(source)
    from lanctl.shared.i18n import t

    names = list(manifest["files"])
    logical = manifest["schemaVersion"] == 2 and manifest["layout"] == "logical"
    if logical and destinations is None:
        raise ValueError(t("LANCTL.STORAGE.ERROR.DESTINATIONS_REQUIRED"))
    targets: list[Path] = []
    for name in names:
        if logical:
            if name not in destinations:
                raise ValueError(t("LANCTL.STORAGE.ERROR.DESTINATION_MISSING", name=name))
            target = Path(destinations[name]).resolve()
            # A supplied map binds the contract, including external workspaces.
            if target in known and known[target] != name:
                raise ValueError(t("LANCTL.STORAGE.ERROR.CONFLICT", path=target))
            known[target] = name
        else:
            pure = Path(name)
            target = (root / pure).resolve()
            if pure.is_absolute() or ".." in pure.parts or not target.is_relative_to(root):
                raise ValueError(t("LANCTL.STORAGE.ERROR.UNSAFE_PATH", path=name))
        targets.append(target)
    if (
        len({os.path.normcase(str(target)) for target in targets}) != len(targets)
        or source.resolve() in targets
    ):
        raise ValueError(t("LANCTL.STORAGE.ERROR.DUPLICATE_TARGET"))
    # Read and validate every payload before touching any destination. Recheck
    # hashes on these exact bytes: verification and import must not use different
    # snapshots if the archive is replaced between opening it and verification.
    payloads: list[bytes] = []
    with zipfile.ZipFile(source) as archive:
        for name, target in zip(names, targets):
            payload = archive.read(f"data/{name}")
            if hashlib.sha256(payload).hexdigest() != manifest["files"][name]:
                raise ValueError(f"hash incorrecto en la exportación: {name}")
            _validate_payload(target, payload, known.get(target))
            payloads.append(payload)
    from lanctl.core.storage_import import commit_import

    if logical:
        pair_paths = [
            Path(destinations[name]).resolve()
            for name in ("devices", "groups")
            if name in destinations
        ]
    else:
        pair_paths = [path for path, contract in known.items() if contract in {"devices", "groups"}]
    if not any(target in pair_paths for target in targets):
        pair_paths = []

    def prepare():
        from lanctl.core.group_database import recover_device_group_transaction

        for path, contract in known.items():
            if contract == "devices" and path in pair_paths:
                recover_device_group_transaction(path)
        for target in targets:
            if target.is_file():
                create_backup(target, directory=root / "import-backups")

    commit_import(root, targets, payloads, prepare=prepare, companions=pair_paths)
    return targets


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
