"""Deadlines and shutdown retain ownership without late session writes."""

from concurrent.futures import CancelledError
from threading import Event
from time import monotonic
from types import SimpleNamespace

import pytest

from lanctl.apps.ip.domain.models import Device
from lanctl.apps.monitor.execution import CheckBudget, CheckDeadlineExceeded, MonitorShutdownPending
from lanctl.apps.monitor.models import (
    CheckResult,
    MonitorProfile,
    MonitorSession,
    MonitorTargetPlan,
)
from lanctl.apps.monitor.scheduler import MonitorScheduler, MonitorWorkerPool
from lanctl.apps.monitor.service import MonitorService


@pytest.fixture(autouse=True)
def isolated_data(tmp_path, monkeypatch):
    from lanctl.core import config

    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LANCTL_SECRET_DIR", str(tmp_path / "secrets"))
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "data/config/config.json")


def session(name="first"):
    return MonitorSession(
        name,
        "run-" + name,
        "manager",
        "project",
        "",
        "",
        "",
        "permanent",
        "observe",
        "2026-11-03T00:00:00+00:00",
    )


def service_with_target(
    monkeypatch, clock=monotonic, metrics=None, assignments=None, sessions=None
):
    profile = MonitorProfile(timeout=0.05, workers=1, jitter=0)
    target = Device("192.0.2.1", mac="02:00:00:00:00:01")
    if assignments is None:
        assignments = SimpleNamespace(plans=lambda owner: [MonitorTargetPlan(target)])
    provider = SimpleNamespace(
        profile=lambda name: profile,
        monitor=lambda: SimpleNamespace(profile="default"),
        retention=dict,
    )
    service = MonitorService(
        config=provider, assignments=assignments, metrics=metrics, sessions=sessions, clock=clock
    )
    history = []
    monkeypatch.setattr(service, "_history", lambda *args: history.append(args))
    return service, history


def test_budget_preserves_numeric_contract_and_shares_cancellation():
    clock = [0.0]
    budget = CheckBudget(0.1, clock=lambda: clock[0])
    assert isinstance(budget, float) and budget == 0.1
    clock[0] = 0.04
    assert budget.checkpoint() == pytest.approx(0.06)
    clock[0] = 0.1
    with pytest.raises(CheckDeadlineExceeded):
        budget.checkpoint()
    budget.cancel()
    with pytest.raises(CancelledError):
        budget.checkpoint()


def test_foreground_exits_after_confirmed_stop_without_signal(monkeypatch):
    service, _ = service_with_target(monkeypatch)
    service._stop_confirmed = False
    stop_event = Event()
    cycles = []

    def cycle():
        cycles.append(True)
        service._stop_confirmed = True

    monkeypatch.setattr(service, "cycle", cycle)
    # A regression reaches sleep; keep the test bounded without leaving a thread.
    monkeypatch.setattr("lanctl.apps.monitor.service.time.sleep", lambda _: stop_event.set())
    service.foreground(poll=0, stop_event=stop_event)
    assert cycles == [True]
    assert not stop_event.is_set()


@pytest.mark.parametrize("state", ["absent", "replacement", "stopping"])
def test_delayed_foreground_child_does_not_resurrect_stopped_session(monkeypatch, state):
    from lanctl.apps.monitor.commands import _run_foreground
    from lanctl.apps.monitor.repositories import InMemorySessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    repository = InMemorySessionRepository()
    owner = session("replacement" if state == "replacement" else "first")
    if state != "absent":
        owner.status = "stopping" if state == "stopping" else "active"
        repository.save(owner)
    monkeypatch.setenv("LANCTL_MONITOR_SESSION_ID", "first")
    result = _run_foreground(SimpleNamespace(), SessionManager(repository))
    assert result["status"] == "cancelled"
    assert result["sessionId"] == "first"
    if state == "replacement":
        assert repository.active() is owner
        assert owner.status == "active"
    else:
        assert repository.active() is None


def test_queue_wait_consumes_deadline_before_second_handler_starts():
    now = [0.0]
    entered, release, completed = Event(), Event(), Event()
    calls, failures = [], []
    pool = MonitorWorkerPool(1, 2)

    def handler(target, budget):
        calls.append(target)
        entered.set()
        assert release.wait(5)

    def failed(task, error, count):
        failures.append(error)
        if len(failures) == 2:
            completed.set()

    scheduler = MonitorScheduler(pool, lambda: now[0], jitter=0, error_handler=failed)
    scheduler.schedule("first", "one", "ping", 5, 0.05, handler)
    scheduler.schedule("second", "two", "ping", 5, 0.05, handler)
    try:
        assert scheduler.tick() == 2
        assert entered.wait(2)
        now[0] = 0.1
        release.set()
        assert completed.wait(2)
        assert calls == ["one"]
        assert all(isinstance(error, CheckDeadlineExceeded) for error in failures)
    finally:
        release.set()
        scheduler.close(timeout=2)


def test_noncooperative_close_is_bounded_and_retains_owned_work():
    entered, release = Event(), Event()
    pool = MonitorWorkerPool(1, 1)

    def blocking():
        entered.set()
        assert release.wait(5)

    try:
        future = pool.submit(blocking)
        assert entered.wait(2)
        started = monotonic()
        with pytest.raises(MonitorShutdownPending):
            pool.close(timeout=0.02)
        assert monotonic() - started < 0.5
        assert pool.closed and not pool.quiescent and not future.done()
        assert pool.submit(lambda: None) is None
    finally:
        release.set()
        assert pool.close(timeout=2)
    assert pool.quiescent


def test_cancel_signals_cooperative_handler_and_drops_failure_callback():
    entered = Event()
    reported = []
    scheduler = MonitorScheduler(
        MonitorWorkerPool(1, 1), monotonic, error_handler=lambda *args: reported.append(args)
    )

    def cooperative(target, budget):
        entered.set()
        budget.wait(10)

    scheduler.schedule("task", "one", "ping", 5, 30, cooperative)
    scheduler.tick()
    assert entered.wait(2)
    assert scheduler.close(timeout=1)
    assert reported == [] and scheduler.pool.quiescent


def test_pending_stop_discards_late_result_and_blocks_next_generation(monkeypatch):
    entered, release = Event(), Event()
    service, history = service_with_target(monkeypatch)

    def measure(check_id, target, timeout, arguments):
        entered.set()
        assert release.wait(5)
        return CheckResult(check_id, target.device_id, True)

    monkeypatch.setattr(service, "_execute_check", measure)
    first = session()
    service.start(first)
    old_generation = service._generation
    try:
        service.scheduler.tick()
        assert entered.wait(2)
        with pytest.raises(MonitorShutdownPending):
            service.stop(timeout=0.02)
        assert first.status == "stopping"
        assert service.session_repo.active() is first
        with pytest.raises(RuntimeError):
            service.start(session("second"))
        assert service.metrics.rows == []
        release.set()
        assert service.stop(timeout=2) is first
        assert first.status == "completed" and first.error is None
        assert service.metrics.rows == []
        assert not any(item[0] == "monitor.check.failed" for item in history)
        service.start(session("second"))
        service._check_failed(
            SimpleNamespace(check_id="ping", target="old"),
            OSError("old failure"),
            1,
            generation=old_generation,
            session=first,
        )
        assert service.metrics.rows == []
    finally:
        release.set()
        service.stop(timeout=2)


def test_expired_measurement_does_not_persist_a_success(monkeypatch):
    now = [0.0]
    service, _ = service_with_target(monkeypatch, clock=lambda: now[0])

    def measure(check_id, target, timeout, arguments):
        now[0] = timeout.deadline + 0.1
        return CheckResult(check_id, target.device_id, True)

    monkeypatch.setattr(service, "_execute_check", measure)
    service.start(session())
    try:
        service.scheduler.tick()
        service.scheduler.pool.close(timeout=2)
        rows = service.metrics.rows
        assert len(rows) == 1
        assert not rows[0][1].success
        assert rows[0][1].error["type"] == "CheckDeadlineExceeded"
    finally:
        service.stop(timeout=2)


def test_expiry_keeps_session_stopping_until_work_drains(monkeypatch):
    entered, release = Event(), Event()
    service, _ = service_with_target(monkeypatch)

    def measure(*args):
        entered.set()
        assert release.wait(5)
        return CheckResult("availability", "one", True)

    monkeypatch.setattr(service, "_execute_check", measure)
    first = session()
    first.expiresAt = "2020-01-01T00:00:00+00:00"
    service.start(first)
    stop = service.stop
    monkeypatch.setattr(service, "stop", lambda status="completed": stop(status, timeout=0.02))
    try:
        service.scheduler.tick()
        assert entered.wait(2)
        assert service.cycle() == 0
        assert first.status == "stopping" and service.scheduler is not None
        release.set()
        stop("expired", timeout=2)
        assert first.status == "expired" and service.scheduler is None
        assert service.metrics.rows == []
    finally:
        release.set()
        stop("expired", timeout=2)


@pytest.mark.parametrize("operation", ["discovery", "maintenance"])
def test_global_operation_does_not_continue_effects_after_stop(monkeypatch, operation):
    entered, release = Event(), Event()
    calls = []

    def block(*args):
        calls.append(args)
        entered.set()
        assert release.wait(5)
        return []

    assignments = SimpleNamespace(plans=lambda owner: [], discover=block)
    from lanctl.apps.monitor.repositories import InMemoryMetricsStore

    metrics = InMemoryMetricsStore()
    metrics.aggregate = block
    cleanup = []
    metrics.cleanup = lambda retention: cleanup.append(retention)
    service, history = service_with_target(monkeypatch, assignments=assignments, metrics=metrics)
    first = session()
    service.start(first)
    handler = service._run_discovery if operation == "discovery" else service._run_maintenance
    service._schedule_global("test.global", "global", operation, 300, 30, handler)
    try:
        service.scheduler.tick()
        assert entered.wait(2)
        with pytest.raises(MonitorShutdownPending):
            service.stop(timeout=0.02)
        assert first.status == "stopping"
        if operation == "discovery":
            assert calls[0][0] is first
        release.set()
        service.stop(timeout=2)
        assert first.status == "completed"
        assert cleanup == []
        assert not any(row[0] == "monitor.discovery.completed" for row in history)
    finally:
        release.set()
        service.stop(timeout=2)


def test_composite_budget_keeps_legacy_per_probe_timeout(monkeypatch):
    from lanctl.apps.monitor import checks

    now = [0.0]
    service, _ = service_with_target(monkeypatch, clock=lambda: now[0])
    probes = []

    def arp_probe(ip, timeout):
        probes.append(float(timeout))
        now[0] += 0.04
        return "02:00:00:00:00:01"

    def ping_probe(ip, timeout):
        probes.append(float(timeout))
        now[0] += 0.04
        return True, 1.0, 64

    monkeypatch.setattr(checks, "active_arp_mac", arp_probe)
    monkeypatch.setattr(checks, "ping_details", ping_probe)
    service.start(session())
    try:
        service.scheduler.tick()
        service.scheduler.pool.close(timeout=2)
        assert probes == [0.05, 0.05]
        assert len(service.metrics.rows) == 1
        assert service.metrics.rows[0][1].success
    finally:
        service.stop(timeout=2)


def test_measurement_accepted_in_time_does_not_become_a_second_failure(monkeypatch):
    now = [0.0]
    service, _ = service_with_target(monkeypatch, clock=lambda: now[0])
    monkeypatch.setattr(
        service,
        "_execute_check",
        lambda check_id, target, timeout, arguments: CheckResult(check_id, target.device_id, True),
    )
    original_write = service.metrics.write

    def slow_commit(result, session_id):
        now[0] = 1000
        original_write(result, session_id)

    monkeypatch.setattr(service.metrics, "write", slow_commit)
    service.start(session())
    try:
        service.scheduler.tick()
        service.scheduler.pool.close(timeout=2)
        assert len(service.metrics.rows) == 1
        assert service.metrics.rows[0][1].success
        assert all(task.failures == 0 for task in service.scheduler.tasks.values())
    finally:
        service.stop(timeout=2)


def test_nested_sqlite_write_is_not_committed_by_inner_context(tmp_path):
    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase

    with MonitorDatabase(tmp_path / "monitor.db") as database:
        metrics = MetricsStore(database)
        with pytest.raises(OSError), database.transaction():
            metrics.write(CheckResult("ping", "device", True), "owner")
            raise OSError("rollback outer generation transaction")
        assert database.execute("SELECT COUNT(*) FROM samples").fetchone()[0] == 0


def test_external_session_stop_revokes_late_measurement(tmp_path, monkeypatch):
    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase, SessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    entered, release = Event(), Event()
    path = tmp_path / "monitor.db"
    with MonitorDatabase(path) as database, MonitorDatabase(path) as other:
        service, _ = service_with_target(
            monkeypatch, metrics=MetricsStore(database), sessions=SessionRepository(database)
        )

        def measure(check_id, target, timeout, arguments):
            entered.set()
            assert release.wait(5)
            return CheckResult(check_id, target.device_id, True)

        monkeypatch.setattr(service, "_execute_check", measure)
        first = session()
        service.start(first)
        try:
            service.scheduler.tick()
            assert entered.wait(2)
            SessionManager(SessionRepository(other)).stop(
                "cancelled", expected_session_id=first.sessionId
            )
            release.set()
            service.scheduler.pool.close(timeout=2)
            assert database.execute("SELECT COUNT(*) FROM samples").fetchone()[0] == 0
            assert database.execute("SELECT COUNT(*) FROM incidents").fetchone()[0] == 0
        finally:
            release.set()
            service.stop(timeout=2)


def test_stop_request_is_not_a_final_session_state(monkeypatch, tmp_path):
    from lanctl.apps.monitor import commands
    from lanctl.apps.monitor.repositories import InMemorySessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    repository = InMemorySessionRepository()
    manager = SessionManager(repository)
    first = manager.start("owner", "project")
    signals = []
    monkeypatch.setattr(
        commands,
        "SingletonLock",
        lambda path: SimpleNamespace(status=lambda: {"running": True, "pid": 12345}),
    )
    monkeypatch.setattr(
        commands,
        "os",
        SimpleNamespace(
            **{**vars(commands.os), "kill": lambda pid, sig: signals.append((pid, sig))}
        ),
    )
    result = commands._stop_monitor(SimpleNamespace(lock=str(tmp_path / "monitor.lock")), manager)
    assert result["status"] == "stopping" and signals
    assert repository.active() is first
    with pytest.raises(RuntimeError):
        manager.start("next", "project")
    manager.stop("cancelled", expected_session_id=first.sessionId)
    assert first.status == "cancelled"


def test_targeted_stop_cannot_close_another_session():
    from lanctl.apps.monitor.repositories import InMemorySessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    manager = SessionManager(InMemorySessionRepository())
    first = manager.start("owner", "project")
    with pytest.raises(RuntimeError):
        manager.stop(expected_session_id="another")
    assert first.status == "active"


def test_new_owner_stop_uses_metadata_without_process_termination(monkeypatch, tmp_path):
    from lanctl.apps.monitor import commands
    from lanctl.apps.monitor.repositories import InMemorySessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    manager = SessionManager(InMemorySessionRepository())
    owner = manager.start("owner", "project")
    service, _ = service_with_target(monkeypatch, sessions=manager.repository)
    service.start(owner, require_existing=True)
    monkeypatch.setattr(
        commands,
        "SingletonLock",
        lambda path: SimpleNamespace(
            status=lambda: {
                "running": True,
                "pid": 12345,
                "controlProtocol": "session-request-v1",
            }
        ),
    )

    def forbidden_signal(*args):
        pytest.fail("cooperative owner must not be terminated by a signal")

    monkeypatch.setattr(
        commands, "os", SimpleNamespace(**{**vars(commands.os), "kill": forbidden_signal})
    )
    try:
        result = commands._stop_monitor(SimpleNamespace(lock=str(tmp_path / "lock")), manager)
        assert result["status"] == "stopping"
        service.foreground(poll=0)
        assert owner.status == "cancelled"
        assert service.scheduler is None
        assert service._stop_confirmed
    finally:
        service.stop()


def test_lock_advertises_cooperative_protocol_only_for_opted_in_owner(tmp_path):
    from lanctl.apps.monitor.lifecycle import SingletonLock

    path = tmp_path / "monitor.lock"
    with SingletonLock(path, control_protocol="session-request-v1"):
        state = SingletonLock(path).status()
        assert state["verified"]
        assert state["controlProtocol"] == "session-request-v1"
    with SingletonLock(path):
        assert "controlProtocol" not in SingletonLock(path).status()


@pytest.mark.parametrize("drains", [False, True])
def test_cooperative_restart_waits_for_owner_before_spawning(monkeypatch, tmp_path, drains):
    from lanctl.apps.monitor import commands
    from lanctl.apps.monitor.repositories import InMemorySessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    manager = SessionManager(InMemorySessionRepository())
    owner = manager.start("owner", "project")
    service, _ = service_with_target(monkeypatch, sessions=manager.repository)
    service.start(owner, require_existing=True)
    elapsed, spawned = [0.0], []
    running = [True]

    def status():
        return {
            "running": running[0],
            "pid": 12345,
            "controlProtocol": "session-request-v1",
        }

    def sleep(seconds):
        elapsed[0] += seconds
        assert owner.status == "stopping"
        if drains:
            service.cycle()
            assert service._stop_confirmed
            running[0] = False

    def spawn(args, *, session_id):
        assert not running[0]
        assert owner.status == "cancelled"
        assert manager.repository.active().sessionId == session_id
        spawned.append(session_id)
        return SimpleNamespace(pid=23456)

    def forbidden_signal(*args):
        pytest.fail("restart must use the advertised cooperative protocol")

    monkeypatch.setattr(commands, "SingletonLock", lambda path: SimpleNamespace(status=status))
    monkeypatch.setattr(
        commands, "time", SimpleNamespace(monotonic=lambda: elapsed[0], sleep=sleep)
    )
    monkeypatch.setattr(
        commands, "os", SimpleNamespace(**{**vars(commands.os), "kill": forbidden_signal})
    )
    monkeypatch.setattr(commands, "_spawn_foreground", spawn)
    try:
        result = commands._restart_action(SimpleNamespace(lock=str(tmp_path / "lock")), manager)
        if drains:
            assert result["status"] == "restarted"
            assert result["sessionId"] == spawned[0]
        else:
            assert result["status"] == "error"
            assert not spawned
            assert manager.repository.active() is owner
            assert owner.status == "stopping"
    finally:
        service.stop()


@pytest.mark.parametrize("transition", ["stopping", "cancelled", "replacement"])
def test_start_rechecks_stale_session_inside_publication_transaction(
    monkeypatch, tmp_path, transition
):
    from lanctl.apps.monitor.database import MonitorDatabase, SessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    path = tmp_path / "monitor.db"
    with MonitorDatabase(path) as database, MonitorDatabase(path) as other:
        repository = SessionRepository(database)
        manager = SessionManager(repository)
        first = manager.start("owner", "project")
        stale = repository.active()
        external = SessionManager(SessionRepository(other))
        if transition == "stopping":
            external.request_stop()
        else:
            external.stop("cancelled")
            if transition == "replacement":
                external.start("successor", "another-project")
        before = [(row.sessionId, row.status) for row in repository.list()]
        service, history = service_with_target(monkeypatch, sessions=repository)
        with pytest.raises(CancelledError):
            service.start(stale, require_existing=True)
        assert service.scheduler is None
        assert service._stop_confirmed
        assert not history
        assert [(row.sessionId, row.status) for row in repository.list()] == before
        assert repository.get(first.sessionId).status != "active"


def test_discovery_rechecks_stop_before_resolving_incident(monkeypatch, tmp_path):
    from contextlib import contextmanager

    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase, SessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    path = tmp_path / "monitor.db"
    with MonitorDatabase(path) as database, MonitorDatabase(path) as other:
        repository = SessionRepository(database)
        owner = SessionManager(repository).start("owner", "project")
        assignments = SimpleNamespace(plans=lambda owner: [], discover=lambda *args: [])
        service, history = service_with_target(
            monkeypatch,
            metrics=MetricsStore(database),
            sessions=repository,
            assignments=assignments,
        )
        service.start(owner, require_existing=True)
        guard = service._effect_guard
        resolutions = []
        monkeypatch.setattr(service.incidents, "resolve", lambda *args: resolutions.append(args))
        crossed = []

        @contextmanager
        def stopped_before_write(generation, session):
            crossed.append(True)
            SessionManager(SessionRepository(other)).request_stop()
            with guard(generation, session) as current:
                yield current

        monkeypatch.setattr(service, "_effect_guard", stopped_before_write)
        try:
            assert service._run_discovery("network", CheckBudget(30)) is None
            assert crossed
            assert not resolutions
            assert not any(row[0] == "monitor.discovery.completed" for row in history)
            assert repository.active().status == "stopping"
        finally:
            service.stop()


@pytest.mark.parametrize("operation", ["aggregate", "cleanup"])
def test_maintenance_rechecks_external_stop_at_write_boundary(monkeypatch, tmp_path, operation):
    from contextlib import contextmanager

    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase, SessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    path = tmp_path / "monitor.db"
    with MonitorDatabase(path) as database, MonitorDatabase(path) as other:
        repository = SessionRepository(database)
        manager = SessionManager(repository)
        owner = manager.start("owner", "project")
        metrics = MetricsStore(database)
        metrics.write(
            CheckResult("ping", "device", True, timestamp="2000-01-01T00:00:00+00:00"),
            owner.sessionId,
        )
        service, _ = service_with_target(monkeypatch, metrics=metrics, sessions=repository)
        service.start(owner, require_existing=True)
        budget = CheckBudget(30)
        service._bind_budget(budget, service._generation, owner)
        guard = budget.effects

        @contextmanager
        def stopped_before_write():
            SessionManager(SessionRepository(other)).request_stop()
            with guard() as current:
                yield current

        budget.effects = stopped_before_write
        try:
            with pytest.raises(CancelledError):
                if operation == "aggregate":
                    metrics.aggregate(budget=budget)
                else:
                    metrics.cleanup({}, budget=budget)
            assert database.execute("SELECT COUNT(*) FROM samples").fetchone()[0] == 1
            assert database.execute("SELECT COUNT(*) FROM metric_aggregates").fetchone()[0] == 0
        finally:
            service.stop()


def test_scanner_stops_starting_new_connections_when_budget_expires():
    from lanctl.apps.ip.infrastructure.services.element_scanner import scan_tcp_ports

    now = [0.0]
    budget = CheckBudget(0.05, clock=lambda: now[0])
    calls = []

    def connector(address, timeout):
        calls.append(address)
        now[0] = 1
        return SimpleNamespace(close=lambda: None)

    with pytest.raises(CheckDeadlineExceeded):
        scan_tcp_ports("192.0.2.1", [22, 80, 443], budget, 1, connector=connector)
    assert calls == [("192.0.2.1", 22)]


def test_discovery_cancellation_drains_nested_workers():
    import ipaddress
    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    from lanctl.apps.ip.infrastructure.services.lan_scanner import LanScanner
    from lanctl.apps.monitor.execution import discovery_progress

    entered, release = Event(), Event()
    budget = CheckBudget(30)
    scanner = LanScanner(ipaddress.IPv4Network("192.0.2.0/30"), 2, 0.1, 10)

    def probe(value):
        if value == 1:
            assert entered.wait(2)
            budget.cancel()
        else:
            entered.set()
            assert release.wait(5)
        return value

    with ThreadPoolExecutor(max_workers=1) as owner:
        future = owner.submit(scanner._parallel, probe, [1, 2], "test", discovery_progress(budget))
        try:
            assert entered.wait(2)
            with pytest.raises(TimeoutError):
                future.result(timeout=0.1)
        finally:
            release.set()
        with pytest.raises(InterruptedError):
            future.result(timeout=2)


def test_sqlite_stop_is_ordered_after_an_accepted_write(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor, TimeoutError

    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase, SessionRepository
    from lanctl.apps.monitor.sessions import SessionManager

    entered, release, closing = Event(), Event(), Event()
    path = tmp_path / "monitor.db"
    with MonitorDatabase(path) as database, MonitorDatabase(path) as other:
        metrics = MetricsStore(database)
        service, _ = service_with_target(
            monkeypatch, metrics=metrics, sessions=SessionRepository(database)
        )
        monkeypatch.setattr(
            service,
            "_execute_check",
            lambda check_id, target, timeout, arguments: CheckResult(
                check_id, target.device_id, True
            ),
        )
        original = metrics.write

        def write(result, owner):
            entered.set()
            assert release.wait(5)
            original(result, owner)

        monkeypatch.setattr(metrics, "write", write)
        first = session()
        service.start(first)

        def stop_other():
            closing.set()
            return SessionManager(SessionRepository(other)).request_stop()

        try:
            service.scheduler.tick()
            assert entered.wait(2)
            with ThreadPoolExecutor(max_workers=1) as requests:
                request = requests.submit(stop_other)
                try:
                    assert closing.wait(2)
                    with pytest.raises(TimeoutError):
                        request.result(timeout=0.1)
                finally:
                    release.set()
                assert request.result(timeout=2).status == "stopping"
            service.stop("cancelled", timeout=2)
            assert database.execute("SELECT COUNT(*) FROM samples").fetchone()[0] == 1
            assert SessionRepository(other).get(first.sessionId).status == "cancelled"
        finally:
            release.set()
            service.stop(timeout=2)


def test_failed_persistence_rolls_back_evaluator_and_sample(tmp_path, monkeypatch):
    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase, SessionRepository

    with MonitorDatabase(tmp_path / "monitor.db") as database:
        service, _ = service_with_target(
            monkeypatch, metrics=MetricsStore(database), sessions=SessionRepository(database)
        )
        first = session()
        service.start(first)
        result = CheckResult("availability", "device", True)
        monkeypatch.setattr(service, "_execute_check", lambda *args: result)
        monkeypatch.setattr(
            service.incidents,
            "resolve",
            lambda *args: (_ for _ in ()).throw(OSError("incident write failed")),
        )
        try:
            with pytest.raises(OSError, match="incident write failed"):
                service._run_check("availability", Device("192.0.2.1"), 1, first)
            assert database.execute("SELECT COUNT(*) FROM samples").fetchone()[0] == 0
            assert "device" not in service.evaluator.states
        finally:
            service.stop(timeout=2)


def test_history_is_pinned_to_session_project(monkeypatch, tmp_path):
    from lanctl.apps.monitor import service as module

    # No real project file is opened by the history adapter.
    provider = SimpleNamespace(
        config={"activeProject": str(tmp_path / "first.vlf")},
        profile=lambda name: MonitorProfile(),
        monitor=lambda: SimpleNamespace(profile="default"),
    )
    service = MonitorService(config=provider, assignments=SimpleNamespace(plans=lambda owner: []))
    projects = []
    monkeypatch.setattr(
        module,
        "HistoryService",
        lambda project: projects.append(project) or SimpleNamespace(write=lambda event: event),
    )
    first = session()
    service.start(first)
    try:
        provider.config["activeProject"] = str(tmp_path / "second.vlf")
        service._history("monitor.test", first, "success", "test")
        assert projects and all(project == str(tmp_path / "first.vlf") for project in projects)
    finally:
        service.stop(timeout=2)


def test_stop_metadata_failure_does_not_release_running_owner(monkeypatch):
    entered, release = Event(), Event()
    service, _ = service_with_target(monkeypatch)

    def measure(check_id, target, timeout, arguments):
        entered.set()
        assert release.wait(5)
        return CheckResult(check_id, target.device_id, True)

    monkeypatch.setattr(service, "_execute_check", measure)
    first = session()
    service.start(first)
    original = service.session_repo.save
    try:
        service.scheduler.tick()
        assert entered.wait(2)
        monkeypatch.setattr(
            service.session_repo,
            "save",
            lambda owner: (_ for _ in ()).throw(OSError("state storage failed")),
        )
        with pytest.raises(MonitorShutdownPending) as caught:
            service.stop("cancelled", timeout=0.02)
        assert isinstance(caught.value.__cause__, OSError)
        assert service.scheduler is not None and not service.scheduler.pool.quiescent
        with pytest.raises(RuntimeError):
            service.start(session("second"))
        monkeypatch.setattr(service.session_repo, "save", original)
        release.set()
        service.stop(timeout=2)
        assert first.status == "cancelled" and service.metrics.rows == []
    finally:
        monkeypatch.setattr(service.session_repo, "save", original)
        release.set()
        service.stop(timeout=2)


def test_failed_commit_restores_evaluator_and_closes_transaction(tmp_path, monkeypatch):
    import sqlite3

    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase, SessionRepository

    with MonitorDatabase(tmp_path / "monitor.db") as database:
        service, _ = service_with_target(
            monkeypatch, metrics=MetricsStore(database), sessions=SessionRepository(database)
        )
        first = session()
        service.start(first)
        result = CheckResult("availability", "device", True)
        monkeypatch.setattr(service, "_execute_check", lambda *args: result)
        reject = [True]

        def authorize(action, operation, *args):
            if action == sqlite3.SQLITE_TRANSACTION and operation == "COMMIT" and reject[0]:
                reject[0] = False
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK

        database.connection.set_authorizer(authorize)
        try:
            with pytest.raises(sqlite3.DatabaseError):
                service._run_check("availability", Device("192.0.2.1"), 1, first)
            assert not database.connection.in_transaction
            assert database.execute("SELECT COUNT(*) FROM samples").fetchone()[0] == 0
            assert "device" not in service.evaluator.states
        finally:
            database.connection.set_authorizer(None)
            service.stop(timeout=2)
