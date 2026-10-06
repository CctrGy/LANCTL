import json
import multiprocessing
import os
import subprocess
import sys
import time
from unittest.mock import patch

import pytest

from lanctl.core.coordination import Coordinator
from lanctl.core.session import Session, overlay_config, prepare_config_save


def _publish_worker(path, number):
    coordinator = Coordinator(path)
    identifier = coordinator.register("lanip", "cli", "home")
    for _ in range(number):
        coordinator.publish(identifier, "LANCTL.Core.Storage.Changed", project="home")
    coordinator.close(identifier)


def test_real_processes_share_ordered_events(tmp_path):
    path = tmp_path / "coordinator.db"
    coordinator = Coordinator(path)
    coordinator.latest()
    processes = [multiprocessing.Process(target=_publish_worker, args=(path, 12)) for _ in range(3)]
    for process in processes:
        process.start()
    for process in processes:
        process.join(20)
        assert process.exitcode == 0
    rows = coordinator.events()
    assert len(rows) == 36
    assert len({row["seq"] for row in rows}) == 36
    assert coordinator.sessions() == []


def test_addressed_commands_owner_and_expiration(tmp_path):
    coordinator = Coordinator(tmp_path / "runtime.db")
    first = coordinator.register("lanip", "gui")
    second = coordinator.register("lanip", "tui")
    coordinator.heartbeat(first, controls=True)
    coordinator.heartbeat(second, controls=True)
    command = coordinator.enqueue(first, "refresh")
    assert coordinator.claim(second) == []
    assert coordinator.claim(first)[0]["id"] == command
    assert coordinator.claim(first) == []
    coordinator.owner = "another-user"
    assert coordinator.sessions() == []
    with pytest.raises(ValueError):
        coordinator.enqueue(first, "refresh")
    with pytest.raises(ValueError):
        coordinator.enqueue(second, "shell", "cmd.exe")


def test_crashed_session_marks_task_interrupted(tmp_path):
    coordinator = Coordinator(tmp_path / "runtime.db")
    identifier = coordinator.register("lanip", "gui")
    coordinator.task(identifier, "LANCTL.Core.Command.Execute", "task")
    with coordinator.connection() as db:
        db.execute("UPDATE sessions SET heartbeat=?", (time.time() - 100,))
    coordinator.maintain()
    assert coordinator.sessions() == []
    assert coordinator.tasks()[0]["state"] == "interrupted"


def test_no_arbitrary_payloads_and_version_rejection(tmp_path):
    coordinator = Coordinator(tmp_path / "runtime.db")
    with pytest.raises(ValueError):
        coordinator.publish("session", "LANCTL.Core.Test.Event", metadata={"password": "secret"})
    with coordinator.connection() as db:
        db.execute("PRAGMA user_version=999")
    with pytest.raises(ValueError, match="versión"):
        coordinator.sessions()


def test_session_project_isolation_and_data_notifications(tmp_path):
    coordinator = Coordinator(tmp_path / "runtime.db")
    first = Session("lanip", "gui", {"activeProject": "A"}, coordinator=coordinator)
    second = Session("lanip", "tui", {"activeProject": "B"}, coordinator=coordinator)
    # Deterministic polling without racing the background heartbeat.
    first.stop_event.set()
    second.stop_event.set()
    first.thread.join()
    second.thread.join()
    try:
        with patch("lanctl.core.session._current", first):
            assert overlay_config({"activeProject": "B"})["activeProject"] == "A"
            saved = prepare_config_save(overlay_config({"workers": 10}), {"activeProject": "B"})
            assert saved["activeProject"] == "B"
            assert first.project == "A"
        received = []
        first.handler = received.append
        coordinator.publish(second.id, "LANCTL.Core.Storage.Changed", project="B")
        first.poll()
        assert received == []
        coordinator.publish(second.id, "LANCTL.Core.Storage.Changed", project="A")
        first.poll()
        assert received == [{"action": "data-changed"}]
    finally:
        first.close()
        second.close()


def test_stale_inventory_snapshot_is_rejected(tmp_path):
    from lanctl.core.database import DeviceDatabase

    path = tmp_path / "devices.json"
    path.write_text("[]")
    database = DeviceDatabase(str(path))
    snapshot = database.load()
    path.write_text(json.dumps([{"MAC": "02:00:00:00:00:01", "IP": "192.168.1.1"}]))
    with pytest.raises(RuntimeError, match="otra sesión"):
        database.save_devices(snapshot)
    assert len(json.loads(path.read_text())) == 1


def test_real_launchers_keep_project_and_share_settings(tmp_path):
    config = tmp_path / "config" / "config.json"
    config.parent.mkdir()
    config.write_text(json.dumps({"activeProject": "first.vlf", "workers": 12}))
    environment = {**os.environ, "LANCTL_DATA_DIR": str(tmp_path)}
    code = """
import json
from lanctl.core.config import load_config, update_config
from lanctl.core.session import coordinated_launcher
@coordinated_launcher('lanip')
def run(argv=None):
    print(json.dumps({'project':load_config()['activeProject']}), flush=True)
    input()
    value=load_config()
    update_config(lambda current: current.update(timeout=1.5))
    print(json.dumps({'project':value['activeProject'], 'workers':value['workers']}), flush=True)
    return 0
run([])
"""
    process = subprocess.Popen(
        [sys.executable, "-c", code],
        env=environment,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert json.loads(process.stdout.readline())["project"] == "first.vlf"
        subprocess.run(
            [
                sys.executable,
                "-c",
                "from lanctl.core.config import update_config; update_config(lambda c: c.update(activeProject='second.vlf', workers=24))",
            ],
            env=environment,
            check=True,
            capture_output=True,
            timeout=15,
        )
        output, error = process.communicate("continue\n", timeout=15)
        assert process.returncode == 0, error
        assert json.loads(output) == {"project": "first.vlf", "workers": 24}
        # Saving unrelated settings must not restore the first session's project.
        assert json.loads(config.read_text())["projects"]["active"] == "second.vlf"
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


def test_admin_control_requires_os_permission(tmp_path):
    with (
        patch("lanctl.core.local_permissions.elevated", return_value=False),
        pytest.raises(PermissionError),
    ):
        Coordinator(tmp_path / "runtime.db", administrative=True)


def test_failed_config_write_does_not_change_session(tmp_path):
    from lanctl.core import config

    coordinator = Coordinator(tmp_path / "runtime.db")
    session = Session("lanip", "gui", {"activeProject": "A"}, coordinator=coordinator)
    try:
        with (
            patch("lanctl.core.session._current", session),
            patch.object(config, "atomic_write_json", side_effect=OSError("disk full")),
            patch.object(config, "_load_config", return_value={}),
        ):
            with pytest.raises(OSError):
                config.save_config.__wrapped__({"activeProject": "B"})
            assert session.project == "A"
    finally:
        session.close()
