import json
from concurrent.futures import Future
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.apps.ip.domain.models import Device
from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase
from lanctl.apps.monitor.models import CheckResult, MonitorProfile, MonitorTargetPlan
from lanctl.apps.monitor.scheduler import MonitorScheduler
from lanctl.apps.monitor.service import MonitorService
from lanctl.apps.monitor.state import StateEvaluator
from lanctl.core.plugins import package


def test_monitor_resolves_current_dhcp_target_for_existing_task():
    service = MonitorService(config=Mock())
    service.scheduler = Mock()
    service.session = Mock(sessionId="test")
    old = Device(ip="192.0.2.30", device_id="stable-id")
    new = Device(ip="192.0.2.31", device_id="stable-id")
    service._schedule_check(MonitorTargetPlan(old), "ping", 60, 1)
    callback = service.scheduler.schedule.call_args.args[5]
    service._schedule_check(MonitorTargetPlan(new), "ping", 60, 1)
    service._run_check = Mock()
    callback("stable-id", 1)
    assert service.scheduler.schedule.call_count == 1
    assert service._run_check.call_args.args[1].ip == new.ip
    service.assignments = Mock(discover=lambda *_: [], plans=lambda *_: [])
    service._history = Mock()
    service._run_discovery("network", 1)
    service.scheduler.cancel.assert_called_once_with("monitor.stable-id.ping")
    service._run_check.reset_mock()
    callback("stable-id", 1)
    service._run_check.assert_not_called()


def test_cancel_inflight_task_prevents_reschedule_and_allows_new_generation():
    class Pool:
        def submit(self, *args, done=None):
            self.future = Future()
            self.future.add_done_callback(done)
            return self.future

    pool = Pool()
    scheduler = MonitorScheduler(pool, lambda: 0, jitter=0)
    scheduler.schedule("task", "device", "ping", 10, 1, lambda *_: None)
    scheduler.tick()
    scheduler.cancel("task")
    old_future = pool.future
    replacement = scheduler.schedule("task", "device", "ping", 20, 1, lambda *_: None)
    old_future.set_result(None)
    assert scheduler.queue == [replacement]
    scheduler.tick()
    scheduler.cancel("task")
    pool.future.set_result(None)
    assert scheduler.queue == []


def test_health_recovers_only_when_all_current_checks_recover():
    evaluator = StateEvaluator(MonitorProfile())
    evaluator.evaluate(CheckResult("ping", "device", True, latencyMs=1500))
    state, *_ = evaluator.evaluate(CheckResult("ping", "device", True, latencyMs=2))
    assert state.health == "healthy"
    evaluator.evaluate(CheckResult("service", "device", False, metrics={"port": 22}))
    state, *_ = evaluator.evaluate(CheckResult("service", "device", True, metrics={"port": 443}))
    assert state.health == "warning"
    state, *_ = evaluator.evaluate(CheckResult("service", "device", True, metrics={"port": 22}))
    assert state.health == "healthy"
    state.health = "maintenance"
    state, *_ = evaluator.evaluate(CheckResult("ping", "device", True, latencyMs=1500))
    assert state.health == "maintenance"


def test_outages_are_incidents_and_durations_fit_the_bucket(tmp_path):
    with MonitorDatabase(tmp_path / "monitor.db") as database:
        metrics = MetricsStore(database)
        for minute in range(5):
            metrics.write(
                CheckResult("ping", "device", False, f"2026-10-14T10:0{minute}:00Z"), "session"
            )
        metrics.aggregate(resolutions=(300,))
        row = database.execute("SELECT * FROM metric_aggregates").fetchone()
        assert row["outage_count"] == 1
        assert row["outage_duration"] == 240
        assert row["packet_loss"] == 100
        metrics.write(CheckResult("ping", "device", True, "2026-10-14T10:06:00Z"), "session")
        metrics.aggregate(resolutions=(300,))
        rows = database.execute("SELECT * FROM metric_aggregates ORDER BY bucket").fetchall()
        assert [row["outage_count"] for row in rows] == [1, 0]
        assert [row["outage_duration"] for row in rows] == [300, 60]


def test_session_report_counts_transitions_not_failed_samples(tmp_path):
    from lanctl.apps.monitor.models import MonitorSession
    from lanctl.apps.monitor.reports import ReportBuilder

    with MonitorDatabase(tmp_path / "monitor.db") as database:
        metrics = MetricsStore(database)
        for second, success in enumerate((True, False, False, True, False)):
            metrics.write(
                CheckResult("ping", "device", success, f"2026-10-14T10:00:0{second}Z"), "session"
            )
        session = MonitorSession(
            "session",
            "run",
            "manager",
            "project",
            "192.0.2.0/24",
            "eth0",
            "192.0.2.2",
            "diagnostic",
            "observe",
            "2026-10-14T10:00:00Z",
        )
        report = ReportBuilder(database, Mock(), SimpleNamespace(list=list)).build(session)
        assert report["summary"]["disconnects"] == 2
        assert report["devices"][0]["outages"] == 2


@pytest.mark.parametrize("failure", ["extract", "publish"])
def test_plugin_update_failure_keeps_previous_installation(tmp_path, monkeypatch, failure):
    source = tmp_path / "source"
    source.mkdir()
    (source / "plugin.info").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "id": "audit.example",
                "version": "1.0.0",
                "lanctl": {"minimumVersion": "0.3.0", "maximumVersion": "0.x"},
            }
        ),
        encoding="utf-8",
    )
    (source / "main.exec").write_text("def activate(api): pass", encoding="utf-8")
    archive = tmp_path / "plugin.lcp"
    package.build_package(source, archive)
    _, destination, _ = package.install_package(archive, tmp_path / "installed")
    original = (destination / "main.exec").read_bytes()
    (source / "main.exec").write_text("def activate(api): api.log('new')", encoding="utf-8")
    package.build_package(source, archive, overwrite=True)
    original_replace = Path.replace

    def fail_publish(path, target):
        if path.parent.name.startswith(".lanctl-lcp-"):
            raise OSError("simulated publish failure")
        return original_replace(path, target)

    def fail_extract(source, target):
        target.write(b"partial")
        raise OSError("simulated disk full")

    with monkeypatch.context() as patch:
        if failure == "extract":
            patch.setattr(package.shutil, "copyfileobj", fail_extract)
        else:
            patch.setattr(Path, "replace", fail_publish)
        with pytest.raises(OSError, match="simulated"):
            package.install_package(archive, tmp_path / "installed")
    assert (destination / "main.exec").read_bytes() == original
    assert (destination / "plugin.info").is_file()
    package.install_package(archive, tmp_path / "installed")
    assert b"new" in (destination / "main.exec").read_bytes()
