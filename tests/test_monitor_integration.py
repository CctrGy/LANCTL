from __future__ import annotations

import json
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.models import Device
from app.monitor.database import IncidentRepository, MetricsStore, MonitorDatabase
from app.monitor.lifecycle import SingletonLock
from app.monitor.models import MonitorProfile, MonitorSession, MonitorTargetPlan
from app.monitor.repositories import (
    InMemoryIncidentRepository,
    InMemoryMetricsStore,
    InMemorySessionRepository,
)
from app.monitor.service import MonitorService
from app.platform.windows import WindowsPlatform


def session():
    return MonitorSession(
        "session-1",
        "run-1",
        "manager-1",
        "project-1",
        "",
        "",
        "",
        "permanent",
        "observe",
        "2026-08-04T10:00:00+00:00",
    )


class ProfileProvider:
    def __init__(self):
        self.normal = MonitorProfile("normal", 60, 7, 300, 600, 3600, 0.2, 1, 0, 2, 1)

    def monitor(self):
        return SimpleNamespace(profile="normal")

    def profile(self, profile_id="normal"):
        if profile_id == "fast":
            return MonitorProfile("fast", 30, 5, 120, 300, 900, 0.1, 1, 0, 2, 1)
        return self.normal

    def retention(self):
        return {"rawSamples": "24h", "fiveMinuteAggregates": "30d", "hourlyAggregates": "365d"}


class PlannedAssignments:
    def __init__(self, target):
        self.target = target

    def plans(self, _session):
        return [
            MonitorTargetPlan(
                self.target,
                "critical",
                "fast",
                (
                    {"type": "port", "interval": "15s", "args": {"port": 22}},
                    {"type": "ping", "interval": "10s"},
                ),
            )
        ]


class MonitorIntegrationTests(unittest.TestCase):
    def test_service_consumes_profile_priority_and_configured_checks(self):
        target = Device("192.168.1.10", mac="02:11:22:33:44:55", alias="NAS")
        service = MonitorService(
            config=ProfileProvider(),
            assignments=PlannedAssignments(target),
            metrics=InMemoryMetricsStore(),
            sessions=InMemorySessionRepository(),
            incidents=InMemoryIncidentRepository(),
            clock=lambda: 0,
        )
        service.start(session())
        tasks = {item.check_id: item for item in service.scheduler.queue}
        self.assertEqual(tasks["availability"].interval, 5)
        self.assertEqual(tasks["port"].interval, 15)
        self.assertEqual(tasks["ping"].interval, 10)
        self.assertEqual(tasks["service"].interval, 300)
        self.assertEqual(tasks["deep"].interval, 900)
        service.scheduler.close()
        service.scheduler = None

    def test_check_exception_is_persisted_as_sample_and_incident(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            MonitorDatabase(Path(temporary) / "monitor.db") as database,
        ):
            metrics = MetricsStore(database)
            incidents = IncidentRepository(database)
            service = MonitorService(
                config=ProfileProvider(),
                metrics=metrics,
                sessions=InMemorySessionRepository(),
                incidents=incidents,
            )
            service.session = session()
            task = SimpleNamespace(check_id="port", target="dev_1")
            with patch("app.monitor.service.HistoryService"):
                service._check_failed(task, OSError("conexión rechazada"), 2)
            row = database.execute("SELECT details FROM samples").fetchone()
            self.assertEqual(json.loads(row["details"])["error"]["failures"], 2)
            self.assertEqual(incidents.list()[0].cause, "check.error.port")

    def test_state_hysteresis_survives_service_restart(self):
        with (
            tempfile.TemporaryDirectory() as temporary,
            MonitorDatabase(Path(temporary) / "monitor.db") as database,
        ):
            with database.transaction():
                database.execute(
                    "INSERT INTO device_state VALUES(?,?,?,?,?,?,?,?)",
                    ("dev_1", "offline", "warning", None, "2026-08-04T10:00:00+00:00", "old", 2, 0),
                )
            service = MonitorService(
                config=ProfileProvider(),
                assignments=SimpleNamespace(targets=lambda _session: []),
                metrics=MetricsStore(database),
                sessions=InMemorySessionRepository(),
                incidents=IncidentRepository(database),
                clock=lambda: 0,
            )
            service.start(session())
            restored = service.evaluator.states["dev_1"]
            self.assertEqual((restored.presence, restored.consecutiveFailures), ("offline", 2))
            service.scheduler.close()
            service.scheduler = None

    def test_schema_one_migrates_and_service_checks_do_not_distort_availability(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "monitor.db"
            connection = sqlite3.connect(path)
            connection.executescript(
                "CREATE TABLE device_state(device_id TEXT PRIMARY KEY,presence TEXT,health TEXT,latency_ms REAL,updated_at TEXT,session_id TEXT);CREATE TABLE samples(sample_id INTEGER PRIMARY KEY AUTOINCREMENT,device_id TEXT NOT NULL,timestamp TEXT NOT NULL,presence INTEGER NOT NULL,latency_ms REAL,check_type TEXT NOT NULL,result TEXT NOT NULL,session_id TEXT,correlation_id TEXT);PRAGMA user_version=1;"
            )
            connection.close()
            with MonitorDatabase(path) as database:
                self.assertEqual(database.execute("PRAGMA user_version").fetchone()[0], 2)
                metrics = MetricsStore(database)
                from app.monitor.models import CheckResult

                metrics.write(CheckResult("availability", "dev_1", True), "session")
                metrics.write(CheckResult("service", "dev_1", False), "session")
                self.assertEqual(metrics.summary()["availability"], 100)

    def test_reused_pid_is_never_considered_a_verified_monitor(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "monitor.lock"
            path.write_text(
                json.dumps({"pid": 123, "identity": {"started": "old", "executable": "lanctl"}}),
                encoding="utf-8",
            )
            with patch(
                "app.monitor.lifecycle._process_identity",
                return_value={"started": "new", "executable": "lanctl"},
            ):
                state = SingletonLock(path).status()
            self.assertFalse(state["running"])
            self.assertTrue(state["stale"])

    def test_windows_service_install_is_idempotent_and_uses_local_service(self):
        responses = []
        query_count = 0

        def completed(arguments):
            nonlocal query_count
            responses.append(arguments)
            if arguments[:2] == ["sc.exe", "query"]:
                query_count += 1
                if query_count == 1:
                    return subprocess.CompletedProcess(
                        arguments, 1060, "", "OpenService FAILED 1060"
                    )
                return subprocess.CompletedProcess(arguments, 0, "STATE : 1 STOPPED", "")
            return subprocess.CompletedProcess(arguments, 0, "OK", "")

        with (
            tempfile.TemporaryDirectory() as temporary,
            patch.object(WindowsPlatform, "_run", side_effect=completed),
        ):
            root = Path(temporary)
            executable = (root / "LANCTL.exe").resolve()
            result = WindowsPlatform().service(
                "install",
                confirm=True,
                command=[str(executable), "monitor", "service-host"],
                data_dir=str(root / "data"),
                start=False,
            )
        create = next(item for item in responses if item[:2] == ["sc.exe", "create"])
        self.assertEqual(result.status, "stopped")
        self.assertIn("LocalService", " ".join(create))
        self.assertIn("service-host", " ".join(create))
        self.assertTrue(
            any(item[0] == "icacls.exe" and "*S-1-5-19:(OI)(CI)M" in item for item in responses)
        )

    def test_windows_service_requires_confirmation_and_inno_registers_lifecycle(self):
        self.assertEqual(WindowsPlatform().service("install", confirm=False).status, "blocked")
        script = (Path(__file__).parents[1] / "packaging/inno/LANCTL.iss").read_text(
            encoding="utf-8"
        )
        self.assertIn("monitor service install --yes", script)
        self.assertIn("monitor service uninstall --yes", script)


if __name__ == "__main__":
    unittest.main()
