from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from lanctl.core.persistence import (
    create_backup,
    diagnose_storage,
    export_storage,
    import_storage,
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


def test_verified_import_replaces_files_and_creates_backups(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    devices = source_root / "database/devices.json"
    groups = source_root / "database/groups.json"
    devices.parent.mkdir(parents=True)
    devices.write_text('[{"IP":"192.0.2.8"}]', encoding="utf-8")
    groups.write_text("[]", encoding="utf-8")
    archive = export_storage([devices, groups], tmp_path / "export.zip")

    destination = tmp_path / "destination"
    old = destination / "devices.json"
    old.parent.mkdir(parents=True)
    old.write_text("[]", encoding="utf-8")
    imported = import_storage(archive, destination)
    assert {item.name for item in imported} == {"devices.json", "groups.json"}
    assert "192.0.2.8" in (destination / "devices.json").read_text(encoding="utf-8")
    assert list((destination / "import-backups").glob("devices.json.*.bak"))


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


def test_import_rollback_preserves_writer_before_lock(tmp_path: Path, monkeypatch) -> None:
    """A real cooperative process writes at the snapshot/lock boundary."""
    import subprocess
    import sys
    from contextlib import contextmanager

    from lanctl.core import file_transaction

    source = tmp_path / "source"
    source.mkdir()
    files = [source / name for name in ("a.json", "b.json", "c.json")]
    for path in files:
        path.write_text("[]", encoding="utf-8")
    archive = export_storage(files, tmp_path / "export.zip")
    root = tmp_path / "destination"
    root.mkdir()
    first = root / "a.json"
    first.write_text('["old"]', encoding="utf-8")
    original_locks = file_transaction.locked_files
    original_write = file_transaction.atomic_write_bytes
    intercepted = False

    @contextmanager
    def interleave(paths, **kwargs):
        nonlocal intercepted
        if not intercepted:
            intercepted = True
            subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import sys; from pathlib import Path; "
                        "from lanctl.core.file_transaction import locked_files, atomic_write_bytes; "
                        "p = Path(sys.argv[1]); "
                        'exec("with locked_files((p,)):\\n'
                        '    atomic_write_bytes(p, b\'[\\"concurrent\\"]\')")'
                    ),
                    str(first),
                ],
                check=True,
                timeout=10,
            )
        with original_locks(paths, **kwargs):
            yield

    failed = False

    def fail_last(target, payload):
        nonlocal failed
        if Path(target).name == "c.json" and not failed:
            failed = True
            raise OSError("injected replacement failure")
        return original_write(target, payload)

    monkeypatch.setattr(file_transaction, "locked_files", interleave)
    monkeypatch.setattr(file_transaction, "atomic_write_bytes", fail_last)
    with pytest.raises(OSError, match="injected replacement"):
        import_storage(archive, root)
    assert json.loads(first.read_bytes()) == ["concurrent"]
    assert not (root / "b.json").exists()
    assert not (root / "c.json").exists()
    # All locks must be available to another process after rollback.
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from lanctl.core.file_transaction import locked_files; "
                'exec("with locked_files(sys.argv[1:], timeout=1):\\n    pass")'
            ),
            *map(str, (root / path.name for path in files)),
        ],
        check=True,
        timeout=10,
    )


def test_import_prevalidates_all_payloads_before_replacement(tmp_path: Path, monkeypatch) -> None:
    from lanctl.core import file_transaction

    source = tmp_path / "source"
    source.mkdir()
    first, last = source / "a.json", source / "z.json"
    first.write_text("[]", encoding="utf-8")
    last.write_text("{broken", encoding="utf-8")
    archive = export_storage([first, last], tmp_path / "export.zip")
    writes = []
    monkeypatch.setattr(file_transaction, "atomic_write_bytes", lambda *args: writes.append(args))
    with pytest.raises(json.JSONDecodeError):
        import_storage(archive, tmp_path / "destination")
    assert writes == []


def test_import_acquires_all_targets_before_snapshot(tmp_path: Path, monkeypatch) -> None:
    from lanctl.core import file_transaction

    source = tmp_path / "source"
    source.mkdir()
    files = [source / name for name in ("z.json", "a.json")]
    for path in files:
        path.write_text("[]", encoding="utf-8")
    archive = export_storage(files, tmp_path / "export.zip")
    destination = tmp_path / "destination"
    acquired = []
    original = file_transaction.InterProcessLock.acquire

    def track(lock):
        result = original(lock)
        acquired.append(lock.path)
        return result

    monkeypatch.setattr(file_transaction.InterProcessLock, "acquire", track)
    import_storage(archive, destination)
    assert acquired[:3] == [
        destination / ".lanctl-import.transaction.lock",
        destination / "a.json.lock",
        destination / "z.json.lock",
    ]


@pytest.mark.parametrize(
    "contract,document",
    [
        ("devices", {}),
        ("devices", [{"IP": "192.0.2.1"}]),
        ("devices", [False]),
        ("devices", [{"IP": "192.0.2.1", "MAC": "invalid"}]),
        ("groups", {}),
        ("groups", [{}]),
        ("groups", [None]),
        ("physical", {}),
        ("physical", {"format": "LANWRE-IDF-DB", "version": 999, "records": {}}),
        ("config", []),
        ("config", {"schemaVersion": 999}),
        ("plugins", {"schemaVersion": 999, "plugins": {}}),
        ("plugins", {"schemaVersion": 1, "plugins": {"test": {"trusted": "yes"}}}),
    ],
)
def test_restore_rejects_invalid_store_without_replacing(tmp_path, contract, document):
    target = tmp_path / "custom-store.data"
    target.write_bytes(b"preserve exact original bytes")
    backup = tmp_path / "backup.bak"
    backup.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError):
        restore_backup(target, backup, contract=contract)
    assert target.read_bytes() == b"preserve exact original bytes"
    check = diagnose_storage([backup], contracts={backup: contract})[0]
    assert not check.valid
    assert check.validation == "failed"


@pytest.mark.parametrize(
    "contract,document",
    [
        ("devices", [{"IP": "192.0.2.1", "MAC": "", "NAME": "legacy name"}]),
        ("groups", [{"name": "BASIC"}]),
        ("physical", {"format": "LANWRE-IDF-DB", "version": 1, "records": {}}),
        ("config", {"network": "192.0.2.0/24"}),
        ("plugins", {}),
        ("plugins", {"schemaVersion": 1, "plugins": {}}),
    ],
)
def test_restore_accepts_historical_store_contracts_without_rewriting(tmp_path, contract, document):
    target = tmp_path / "arbitrary.data"
    backup = tmp_path / "backup.bak"
    payload = (json.dumps(document, indent=4) + "\n").encode()
    backup.write_bytes(payload)
    restore_backup(target, backup, contract=contract)
    assert target.read_bytes() == payload
    assert backup.read_bytes() == payload
    check = diagnose_storage([target], contracts={target: contract})[0]
    assert check.valid and check.validation == "functional"


def test_restore_validates_one_snapshot_after_lock(tmp_path, monkeypatch):
    from contextlib import contextmanager

    from lanctl.core import persistence
    from lanctl.core.file_transaction import locked_files

    target, backup = tmp_path / "devices.json", tmp_path / "backup.bak"
    target.write_bytes(b"[]")
    backup.write_bytes(b"[]")
    reads = []
    original_read = Path.read_bytes

    def read(path):
        if path == backup:
            reads.append(path)
        return original_read(path)

    @contextmanager
    def replace_before_acquire(paths):
        # A cooperative writer finishes before restore acquires the lock.
        backup.write_bytes(b"{}")
        with locked_files(paths):
            yield

    monkeypatch.setattr(persistence, "locked_files", replace_before_acquire)
    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(ValueError):
        restore_backup(target, backup, contract="devices")
    assert reads == [backup]
    assert target.read_bytes() == b"[]"


def test_diagnosis_does_not_claim_unknown_json_is_functional(tmp_path):
    target = tmp_path / "unknown.json"
    target.write_bytes(b"{}")
    check = diagnose_storage([target], contracts={})[0]
    assert check.valid
    assert check.validation == "syntax-only"


def test_import_validates_known_contracts_before_any_write(tmp_path, monkeypatch):
    from lanctl.core import file_transaction

    source = tmp_path / "source"
    source.mkdir()
    devices, groups = source / "devices.json", source / "groups.json"
    devices.write_bytes(b"[]")
    groups.write_bytes(b"{}")
    archive = export_storage([devices, groups], tmp_path / "export.zip")
    destination = tmp_path / "destination"
    writes = []
    monkeypatch.setattr(file_transaction, "atomic_write_bytes", lambda *args: writes.append(args))
    with pytest.raises(ValueError):
        import_storage(
            archive,
            destination,
            contracts={
                destination / "devices.json": "devices",
                destination / "groups.json": "groups",
            },
        )
    assert writes == []


def test_configured_contracts_follow_custom_paths(tmp_path, monkeypatch):
    from lanctl.core import config
    from lanctl.core.storage_validation import configured_contracts

    devices = tmp_path / "external" / "anything.data"
    groups = tmp_path / "group-store"
    monkeypatch.setattr(
        config, "load_config", lambda: {"database": str(devices), "groups": str(groups)}
    )
    contracts = configured_contracts()
    assert contracts[devices] == "devices"
    assert contracts[groups] == "groups"
    devices.parent.mkdir()
    devices.write_bytes(b"[]")
    backup = tmp_path / "backup.bak"
    backup.write_bytes(b"{}")
    with pytest.raises(ValueError):
        restore_backup(devices, backup)
    assert not diagnose_storage([backup], contracts={backup: "devices"})[0].valid
    assert devices.read_bytes() == b"[]"


def test_restore_writes_exact_validated_bytes_even_if_backup_changes(tmp_path, monkeypatch):
    from lanctl.core import persistence

    target, backup = tmp_path / "devices.json", tmp_path / "backup.bak"
    target.write_bytes(b"[]")
    payload = b'[{"IP":"192.0.2.1","MAC":""}]'
    backup.write_bytes(payload)
    original = persistence._validate_payload

    def replace_after_validation(path, observed, contract):
        result = original(path, observed, contract)
        # Simulate a writer ignoring locks. No second read may import these bytes.
        backup.write_bytes(b"{}")
        return result

    monkeypatch.setattr(persistence, "_validate_payload", replace_after_validation)
    restore_backup(target, backup, contract="devices")
    assert target.read_bytes() == payload
    assert backup.read_bytes() == b"{}"


def test_restore_backup_is_locked_against_cooperative_writer(tmp_path, monkeypatch):
    import subprocess
    import sys

    from lanctl.core import persistence

    target, backup = tmp_path / "devices.json", tmp_path / "backup.bak"
    backup.write_bytes(b"[]")
    original = persistence._validate_payload

    def check_lock(path, observed, contract):
        child = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys; from lanctl.core.file_transaction import locked_file;\ntry:\n with locked_file(sys.argv[1], timeout=0.05): pass\nexcept TimeoutError:\n sys.exit(0)\nsys.exit(1)",
                str(backup),
            ],
            timeout=10,
            check=False,
        )
        assert child.returncode == 0
        return original(path, observed, contract)

    monkeypatch.setattr(persistence, "_validate_payload", check_lock)
    restore_backup(target, backup, contract="devices")
    assert target.read_bytes() == b"[]"


def test_unknown_contract_cannot_replace_store(tmp_path):
    target, backup = tmp_path / "target", tmp_path / "backup"
    target.write_bytes(b"preserve")
    backup.write_bytes(b"{}")
    with pytest.raises(ValueError):
        restore_backup(target, backup, contract="future-version")
    assert target.read_bytes() == b"preserve"


def test_explicit_export_root_preserves_missing_optional_directories(tmp_path):
    root = tmp_path / "source"
    devices, groups = root / "database/devices.json", root / "database/groups.json"
    devices.parent.mkdir(parents=True)
    devices.write_bytes(b"[]")
    groups.write_bytes(b"[]")
    archive = export_storage(
        [devices, groups, root / "plugins/registry.json"], tmp_path / "export.zip", source_root=root
    )
    manifest = verify_export(archive)
    assert manifest["schemaVersion"] == 2 and manifest["layout"] == "relative"
    assert set(manifest["files"]) == {"database/devices.json", "database/groups.json"}
    destination = tmp_path / "destination"
    import_storage(archive, destination, contracts={})
    assert (destination / "database/devices.json").read_bytes() == b"[]"
    assert not (destination / "devices.json").exists()


def test_logical_export_round_trip_external_workspace(tmp_path):
    source = tmp_path / "external-source" / "custom-name.data"
    source.parent.mkdir()
    source.write_bytes(b'[{"IP":"192.0.2.1","MAC":""}]')
    archive = export_storage(
        [source],
        tmp_path / "logical.zip",
        destinations={"devices": source, "groups": tmp_path / "absent"},
    )
    manifest = verify_export(archive)
    assert manifest["schemaVersion"] == 2 and manifest["layout"] == "logical"
    assert set(manifest["files"]) == {"devices"}
    target = tmp_path / "external-target" / "different-name.data"
    imported = import_storage(
        archive, tmp_path / "ordinary-root", contracts={}, destinations={"devices": target}
    )
    assert imported == [target]
    assert target.read_bytes() == source.read_bytes()
    assert not (tmp_path / "ordinary-root/devices").exists()


def test_logical_import_requires_complete_map_and_rejects_aliases(tmp_path):
    devices, groups = tmp_path / "devices", tmp_path / "groups"
    devices.write_bytes(b"[]")
    groups.write_bytes(b"[]")
    archive = export_storage(
        [devices, groups],
        tmp_path / "logical.zip",
        destinations={"devices": devices, "groups": groups},
    )
    root, target = tmp_path / "root", tmp_path / "target"
    for mapping in (None, {"devices": target}, {"devices": target, "groups": target}):
        with pytest.raises(ValueError):
            import_storage(archive, root, contracts={}, destinations=mapping)
    assert not target.exists()


def test_logical_import_validates_without_filename_heuristics(tmp_path):
    source = tmp_path / "unknown.data"
    source.write_bytes(b"{}")
    archive = export_storage([source], tmp_path / "export.zip", destinations={"devices": source})
    target = tmp_path / "target.data"
    target.write_bytes(b"[]")
    with pytest.raises(ValueError):
        import_storage(archive, tmp_path / "root", contracts={}, destinations={"devices": target})
    assert target.read_bytes() == b"[]"


def test_old_export_keeps_original_relative_layout(tmp_path):
    source = tmp_path / "source/database/devices.json"
    source.parent.mkdir(parents=True)
    source.write_bytes(b"[]")
    archive = export_storage([source], tmp_path / "old.zip")
    assert verify_export(archive)["schemaVersion"] == 1
    root = tmp_path / "destination"
    import_storage(archive, root, contracts={})
    assert (root / "devices.json").exists()
    assert not (root / "database/devices.json").exists()


@pytest.mark.parametrize(
    "name",
    [
        "../escape.json",
        "/absolute.json",
        "C:/escape.json",
        "C:\\escape.json",
        "folder/../escape.json",
        "folder//file.json",
    ],
)
def test_export_manifest_rejects_unsafe_destinations(tmp_path, name):
    import hashlib

    archive = tmp_path / "unsafe.zip"
    payload = b"[]"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr(
            "manifest.json",
            json.dumps(
                {
                    "schemaVersion": 2,
                    "layout": "relative",
                    "files": {name: hashlib.sha256(payload).hexdigest()},
                }
            ),
        )
        output.writestr(f"data/{name}", payload)
    with pytest.raises(ValueError):
        import_storage(archive, tmp_path / "destination", contracts={})


def test_explicit_export_rejects_source_outside_root(tmp_path):
    source = tmp_path / "external.json"
    source.write_bytes(b"[]")
    with pytest.raises(ValueError):
        export_storage([source], tmp_path / "export.zip", source_root=tmp_path / "other")


def test_database_cli_exports_and_imports_current_logical_destinations(
    tmp_path, monkeypatch, capsys
):
    from argparse import Namespace

    from lanctl.apps.ip.interfaces.cli.commands import database as command
    from lanctl.core import config

    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "data/config/config.json")
    devices = tmp_path / "external" / "custom.data"
    groups = tmp_path / "external" / "groups.data"
    devices.parent.mkdir()
    devices.write_bytes(b'[{"IP":"192.0.2.1","MAC":""}]')
    groups.write_bytes(b"[]")
    settings = {"database": str(devices), "groups": str(groups)}
    monkeypatch.setattr(config, "load_config", lambda: dict(settings))
    monkeypatch.setattr(command, "load_config", lambda: dict(settings))
    archive = tmp_path / "cli.zip"
    args = Namespace(verify=None, export=str(archive), import_file=None, restore=None, yes=True)
    assert command.run_database(args) == 0
    assert verify_export(archive)["layout"] == "logical"
    original = devices.read_bytes()
    devices.write_bytes(b"[]")
    args.export, args.import_file = None, str(archive)
    assert command.run_database(args) == 0
    assert devices.read_bytes() == original
    assert not (tmp_path / "data/devices").exists()
    capsys.readouterr()
