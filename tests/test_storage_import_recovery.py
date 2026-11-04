"""Crash recovery uses fresh interpreters, without exception-driven rollback."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from lanctl.core.persistence import export_storage, import_storage
from lanctl.core.storage_import import JOURNAL_NAME, marker_path, recover_for_paths, recover_journal

CRASH_SCRIPT = r"""
import json, os, sys
from pathlib import Path
from lanctl.core import file_transaction as ft
from lanctl.core.persistence import import_storage
from lanctl.core.storage_import import JOURNAL_NAME, MARKER_SUFFIX
archive, root, devices, groups, stage = sys.argv[1:]
original_write, original_unlink = ft.atomic_write_bytes, Path.unlink
markers = 0

def write(path, payload):
    global markers
    result = original_write(path, payload)
    path = Path(path)
    hit = ""
    if path.name == JOURNAL_NAME:
        hit = "journal" if json.loads(payload)["phase"] == "prepared" else "commit"
    elif path.name.endswith(MARKER_SUFFIX):
        markers += 1
        hit = "marker" + str(markers)
    elif path == Path(devices) and (Path(root) / JOURNAL_NAME).exists():
        hit = "data1"
    elif path == Path(groups):
        hit = "data2"
    if hit == stage:
        os._exit(73)
    return result

def unlink(path, *a, **kw):
    result = original_unlink(path, *a, **kw)
    if stage == "cleanup" and path.name.endswith(MARKER_SUFFIX):
        os._exit(73)
    return result

ft.atomic_write_bytes, Path.unlink = write, unlink
import_storage(archive, root, contracts={}, destinations={"devices": devices, "groups": groups})
"""


def setup_import(tmp_path, *, absent=False, external=False):
    source = tmp_path / "source"
    source.mkdir()
    devices, groups = source / "devices", source / "groups"
    devices.write_bytes(b'[{"IP":"192.0.2.2","MAC":""}]')
    groups.write_bytes(b'[{"name":"NEW"}]')
    archive = export_storage(
        [devices, groups],
        tmp_path / "export.zip",
        destinations={"devices": devices, "groups": groups},
    )
    root = tmp_path / "root"
    destination = tmp_path / "outside" if external else root
    destination.mkdir()
    devices, groups = destination / "devices.json", destination / "groups.json"
    old_devices = b'[{"IP":"192.0.2.1","MAC":""}]'
    old_groups = b'[{"name":"OLD"}]'
    devices.write_bytes(old_devices)
    if not absent:
        groups.write_bytes(old_groups)
    return archive, root, devices, groups, old_devices, old_groups


def crash_import(archive, root, devices, groups, stage):
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            CRASH_SCRIPT,
            str(archive),
            str(root),
            str(devices),
            str(groups),
            stage,
        ],
        timeout=15,
    )
    assert result.returncode == 73


@pytest.mark.parametrize(
    "stage", ["journal", "marker1", "marker2", "data1", "data2", "commit", "cleanup"]
)
@pytest.mark.parametrize("external", [False, True])
def test_real_crash_recovers_one_generation(tmp_path, stage, external):
    archive, root, devices, groups, old_devices, old_groups = setup_import(
        tmp_path, external=external
    )
    crash_import(archive, root, devices, groups, stage)
    # The journal-only stage has no target markers yet and has changed no data.
    # A subsequent import recovers that root journal. Other stages recover by
    # opening a store in a fresh launcher interpreter.
    recovery = r"""
import sys
from pathlib import Path
from lanctl.core.database import DeviceDatabase
from lanctl.core.group_database import GroupDatabase
from lanctl.core.storage_import import recover_journal
root, devices, groups, stage = sys.argv[1:]
if stage == 'journal':
    recover_journal(Path(root) / '.lanctl-import.transaction')
GroupDatabase(groups, DeviceDatabase(devices)).load()
"""
    subprocess.run(
        [sys.executable, "-c", recovery, str(root), str(devices), str(groups), stage],
        check=True,
        timeout=15,
    )
    committed = stage in {"commit", "cleanup"}
    assert json.loads(devices.read_bytes())[0]["IP"] == ("192.0.2.2" if committed else "192.0.2.1")
    assert json.loads(groups.read_bytes())[0]["name"] == ("NEW" if committed else "OLD")
    if not committed:
        assert devices.read_bytes() == old_devices
        assert groups.read_bytes() == old_groups
    assert not (root / JOURNAL_NAME).exists()
    assert not marker_path(devices).exists() and not marker_path(groups).exists()
    assert not recover_journal(root / JOURNAL_NAME)
    assert len(list((root / "import-backups").glob("*.bak"))) == 2


def test_recovery_removes_initially_absent_store(tmp_path):
    archive, root, devices, groups, old_devices, _ = setup_import(tmp_path, absent=True)
    crash_import(archive, root, devices, groups, "data2")
    recover_for_paths((groups,))
    assert devices.read_bytes() == old_devices
    assert not groups.exists()


@pytest.mark.parametrize("stage", ["restore1", "restore2", "rollback-phase", "rollback-cleanup"])
def test_recovery_is_idempotent_after_real_second_crash(tmp_path, stage):
    archive, root, devices, groups, old_devices, old_groups = setup_import(tmp_path)
    crash_import(archive, root, devices, groups, "data2")
    recovery_crash = r"""
import os, sys
from pathlib import Path
from lanctl.core import file_transaction as ft
from lanctl.core.storage_import import recover_for_paths
original = ft.atomic_write_bytes

def write(path, payload):
    result = original(path, payload)
    target = Path(path)
    hit = "restore1" if target == Path(sys.argv[1]) else "restore2" if target == Path(sys.argv[2]) else "rollback-phase" if target.name == '.lanctl-import.transaction' else ""
    if hit == sys.argv[3]:
        os._exit(74)
    return result
original_unlink = Path.unlink
def unlink(path, *args, **kwargs):
    result = original_unlink(path, *args, **kwargs)
    if sys.argv[3] == "rollback-cleanup" and path.name.endswith('.lanctl-import.pending'):
        os._exit(74)
    return result
ft.atomic_write_bytes, Path.unlink = write, unlink
recover_for_paths((Path(sys.argv[1]),))
"""
    result = subprocess.run(
        [sys.executable, "-c", recovery_crash, str(devices), str(groups), stage], timeout=15
    )
    assert result.returncode == 74
    assert (root / JOURNAL_NAME).exists()
    recover_for_paths((groups,))
    assert devices.read_bytes() == old_devices and groups.read_bytes() == old_groups
    assert not (root / JOURNAL_NAME).exists()


def test_failed_rollback_retains_evidence_and_can_be_retried(tmp_path, monkeypatch):
    from lanctl.core import file_transaction as ft

    archive, root, devices, groups, old_devices, old_groups = setup_import(tmp_path)
    original = ft.atomic_write_bytes
    failed = False

    def write(path, payload):
        nonlocal failed
        if Path(path) == groups and not failed:
            failed = True
            raise OSError("primary replacement failure")
        if failed and Path(path) == devices:
            raise PermissionError("rollback failure")
        return original(path, payload)

    monkeypatch.setattr(ft, "atomic_write_bytes", write)
    with pytest.raises(PermissionError, match="rollback failure") as caught:
        import_storage(
            archive, root, contracts={}, destinations={"devices": devices, "groups": groups}
        )
    assert caught.value.__context__ is not None
    assert (root / JOURNAL_NAME).exists()
    assert marker_path(devices).exists()
    monkeypatch.setattr(ft, "atomic_write_bytes", original)
    recover_for_paths((devices,))
    assert devices.read_bytes() == old_devices and groups.read_bytes() == old_groups


def test_invalid_marker_does_not_write_other_destinations(tmp_path):
    archive, root, devices, groups, _, _ = setup_import(tmp_path)
    crash_import(archive, root, devices, groups, "data1")
    other = tmp_path / "unrelated.json"
    other.write_bytes(b"private unchanged")
    marker = marker_path(groups)
    pointer = json.loads(marker.read_bytes())
    pointer["target"] = str(other)
    marker.write_text(json.dumps(pointer), encoding="utf-8")
    before = devices.read_bytes()
    with pytest.raises(ValueError):
        recover_for_paths((devices,))
    assert devices.read_bytes() == before
    assert other.read_bytes() == b"private unchanged"
    assert (root / JOURNAL_NAME).exists()


@pytest.mark.parametrize("kind", ["config", "plugins", "physical", "devices"])
def test_store_reader_recovers_before_exposing_pending_bytes(tmp_path, monkeypatch, kind):
    root = tmp_path / "root"
    root.mkdir()
    first, second = root / "first.json", root / "second.db"
    first.write_bytes(b'[{"IP":"192.0.2.1","MAC":""}]')
    old = {
        "config": b'{"schemaVersion":2}',
        "plugins": b'{"schemaVersion":1,"plugins":{}}',
        "physical": b'{"format":"LANWRE-IDF-DB","version":1,"records":{}}',
        "devices": b'[{"IP":"192.0.2.1","MAC":""}]',
    }[kind]
    second.write_bytes(old)
    script = r"""
import os, sys
from pathlib import Path
from lanctl.core import file_transaction as ft
from lanctl.core.storage_import import commit_import
root, first, second = map(Path, sys.argv[1:])
original = ft.atomic_write_bytes
def write(path, payload):
    result = original(path, payload)
    if Path(path) == first:
        os._exit(73)
    return result
ft.atomic_write_bytes = write
commit_import(root, [first, second], [b'[{"IP":"192.0.2.2","MAC":""}]', b'{}'])
"""
    result = subprocess.run(
        [sys.executable, "-c", script, str(root), str(first), str(second)], timeout=15
    )
    assert result.returncode == 73
    if kind == "config":
        from lanctl.core import config

        monkeypatch.setattr(config, "CONFIG_PATH", second)
        config._load_config()
    elif kind == "plugins":
        from lanctl.core.plugins.manager import PluginManager

        PluginManager(tmp_path / "installed", second)._read_registry()
    elif kind == "physical":
        from lanctl.apps.wire.xfile import read

        read(second)
    else:
        from lanctl.core.database import DeviceDatabase

        DeviceDatabase(str(second)).load()
    assert first.read_bytes() == b'[{"IP":"192.0.2.1","MAC":""}]'
    assert second.read_bytes() == old
    assert not (root / JOURNAL_NAME).exists()


def test_bad_snapshot_hash_fails_before_any_restore(tmp_path):
    archive, root, devices, groups, _, _ = setup_import(tmp_path)
    crash_import(archive, root, devices, groups, "data1")
    journal = root / JOURNAL_NAME
    document = json.loads(journal.read_bytes())
    document["entries"][1]["before"]["sha256"] = "0" * 64
    journal.write_text(json.dumps(document), encoding="utf-8")
    current = devices.read_bytes()
    with pytest.raises(ValueError):
        recover_for_paths((devices,))
    assert devices.read_bytes() == current
    assert journal.exists()


def test_locked_writer_recovers_before_mutating_a_crashed_import(tmp_path):
    from lanctl.core.file_transaction import atomic_write_bytes, locked_file

    archive, root, devices, groups, _, _ = setup_import(tmp_path)
    crash_import(archive, root, devices, groups, "data1")
    with locked_file(groups):
        atomic_write_bytes(groups, b'[{"name":"LATER"}]')
    assert json.loads(devices.read_bytes())[0]["IP"] == "192.0.2.1"
    assert json.loads(groups.read_bytes())[0]["name"] == "LATER"
    assert not (root / JOURNAL_NAME).exists()


@pytest.mark.parametrize("pause_stage", ["journal", "data1"])
def test_reader_waiting_on_import_recovers_after_crash_or_sees_commit(tmp_path, pause_stage):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError
    from time import monotonic, sleep

    from lanctl.core.file_transaction import locked_file

    archive, root, devices, groups, _, _ = setup_import(tmp_path)
    ready, release = tmp_path / "ready", tmp_path / "release"
    script = CRASH_SCRIPT.replace(
        "if hit == stage:\n        os._exit(73)",
        """if hit == stage:
        import time
        Path(sys.argv[6]).write_text("ready")
        deadline = time.monotonic() + 10
        while not Path(sys.argv[7]).exists():
            if time.monotonic() > deadline:
                os._exit(75)
            time.sleep(.01)
        if stage == "journal":
            # Publish markers, then die at the first data write instead.
            stage = "data1-crash"
    if hit == "data1" and stage == "data1-crash":
        os._exit(73)""",
    )
    script = script.replace("= sys.argv[1:]", "= sys.argv[1:6]").replace(
        "global markers", "global markers, stage"
    )
    writer = subprocess.Popen(
        [
            sys.executable,
            "-c",
            script,
            str(archive),
            str(root),
            str(devices),
            str(groups),
            pause_stage,
            str(ready),
            str(release),
        ]
    )
    try:
        deadline = monotonic() + 10
        while not ready.exists() and writer.poll() is None and monotonic() < deadline:
            sleep(0.01)
        assert ready.exists()

        def read():
            with locked_file(groups):
                return devices.read_bytes(), groups.read_bytes()

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(read)
            try:
                with pytest.raises(TimeoutError):
                    future.result(timeout=0.1)
            finally:
                release.write_text("continue")
            observed_devices, observed_groups = future.result(timeout=15)
        writer.wait(timeout=10)
        assert writer.returncode == (73 if pause_stage == "journal" else 0)
        assert json.loads(observed_devices)[0]["IP"] == (
            "192.0.2.1" if pause_stage == "journal" else "192.0.2.2"
        )
        assert json.loads(observed_groups)[0]["name"] == (
            "OLD" if pause_stage == "journal" else "NEW"
        )
    finally:
        release.write_text("continue")
        if writer.poll() is None:
            writer.kill()
        writer.wait(timeout=10)


def test_old_device_group_journal_is_resolved_before_import_snapshot(tmp_path):
    from lanctl.core.group_database import _encoded_snapshot, _journal_path

    archive, root, devices, groups, old_devices, old_groups = setup_import(tmp_path)
    journal = _journal_path(devices)
    journal.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "devicesPath": str(devices),
                "groupsPath": str(groups),
                "before": {
                    "devices": _encoded_snapshot(old_devices),
                    "groups": _encoded_snapshot(old_groups),
                },
            }
        ),
        encoding="utf-8",
    )
    devices.write_bytes(b'[{"IP":"192.0.2.99","MAC":""}]')
    crash_import(archive, root, devices, groups, "data1")
    assert not journal.exists()
    recover_for_paths((devices,))
    assert devices.read_bytes() == old_devices
    assert groups.read_bytes() == old_groups
    assert any(
        path.read_bytes() == old_devices
        for path in (root / "import-backups").glob("devices.json.*.bak")
    )


def test_project_fingerprint_does_not_bypass_failed_recovery(tmp_path):
    from lanctl.core.projects.save_policy import workspace_fingerprint
    from lanctl.core.storage_import import ImportRecoveryError

    archive, root, devices, groups, _, _ = setup_import(tmp_path)
    crash_import(archive, root, devices, groups, "data1")
    marker_path(groups).write_bytes(b"{}")
    with pytest.raises(ImportRecoveryError):
        workspace_fingerprint(
            {"projectWorkspace": {"database": str(devices), "groups": str(groups)}}
        )
