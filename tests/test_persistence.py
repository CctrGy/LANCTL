from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from lanctl.core.persistence import (
    create_backup,
    diagnose_storage,
    export_storage,
    migrate_schema,
    restore_backup,
    schema_document,
    verify_export,
)


def test_backup_and_restore_validate_json(tmp_path: Path) -> None:
    source = tmp_path / "devices.json"
    source.write_text('[{"IP":"192.0.2.1"}]', encoding="utf-8")
    backup = create_backup(source)
    source.write_text("{broken", encoding="utf-8")
    restore_backup(source, backup)
    assert json.loads(source.read_text(encoding="utf-8"))[0]["IP"] == "192.0.2.1"


def test_invalid_backup_cannot_replace_json(tmp_path: Path) -> None:
    target = tmp_path / "devices.json"
    target.write_text("[]", encoding="utf-8")
    backup = tmp_path / "bad.bak"
    backup.write_text("broken", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        restore_backup(target, backup)
    assert target.read_text(encoding="utf-8") == "[]"


def test_verified_export_detects_tampering(tmp_path: Path) -> None:
    first = tmp_path / "data/devices.json"
    second = tmp_path / "data/groups.json"
    first.parent.mkdir()
    first.write_text("[]", encoding="utf-8")
    second.write_text("[]", encoding="utf-8")
    archive = export_storage([first, second], tmp_path / "backup.zip")
    assert len(verify_export(archive)["files"]) == 2

    corrupted = tmp_path / "corrupted.zip"
    with zipfile.ZipFile(archive) as source, zipfile.ZipFile(corrupted, "w") as output:
        for name in source.namelist():
            payload = b"tampered" if name == "data/devices.json" else source.read(name)
            output.writestr(name, payload)
    with pytest.raises(ValueError, match="hash incorrecto"):
        verify_export(corrupted)


def test_diagnosis_and_schema_document(tmp_path: Path) -> None:
    valid = tmp_path / "valid.json"
    corrupt = tmp_path / "corrupt.json"
    valid.write_text("{}", encoding="utf-8")
    corrupt.write_text("{", encoding="utf-8")
    checks = diagnose_storage([valid, corrupt, tmp_path / "missing.json"])
    assert [check.valid for check in checks] == [True, False, False]
    assert schema_document()["schemaVersion"] == 1
    assert set(schema_document()["scopes"]) == {"global", "user", "project"}


def test_schema_migration_creates_backup_and_rejects_future_versions(tmp_path: Path) -> None:
    marker = tmp_path / "storage-schema.json"
    marker.write_text('{"schemaVersion": 0}', encoding="utf-8")
    backup = migrate_schema(marker)
    assert backup is not None and backup.is_file()
    assert json.loads(marker.read_text(encoding="utf-8"))["schemaVersion"] == 1

    marker.write_text('{"schemaVersion": 999}', encoding="utf-8")
    with pytest.raises(ValueError, match="incompatible"):
        migrate_schema(marker)
