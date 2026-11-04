from __future__ import annotations

import threading
import time
from contextlib import contextmanager, nullcontext, suppress
from copy import deepcopy

from lanctl.core.history import HistoryEvent, HistoryService

from .checks import CheckRegistry, arp, availability, deep, ping, service, tcp_port
from .configuration import parse_duration
from .execution import CheckBudget, MonitorShutdownPending, remaining_timeout
from .incidents import IncidentManager
from .models import CheckResult, CheckSpec, DeviceState, MonitorTargetPlan
from .repositories import (
    InMemoryIncidentRepository,
    InMemoryMetricsStore,
    InMemorySessionRepository,
    NullReportBuilder,
)
from .scheduler import MonitorScheduler, MonitorWorkerPool
from .sessions import SessionManager
from .state import StateEvaluator


class MonitorService:
    """Motor permanente con planificación acotada y estado observable."""

    def __init__(
        self,
        *,
        config=None,
        assignments=None,
        metrics=None,
        sessions=None,
        incidents=None,
        reports=None,
        clock=time.monotonic,
    ):
        if config is None:
            try:
                from .configuration import ConfigProvider

                config = ConfigProvider()
            except (ValueError, OSError):
                config = ConfigProvider({"monitor": {}})
        self.config = config
        self.assignments = assignments
        self.metrics = metrics or InMemoryMetricsStore()
        self.session_repo = sessions or InMemorySessionRepository()
        self.incident_repo = incidents or InMemoryIncidentRepository()
        self.reports = reports or NullReportBuilder()
        self.clock = clock
        self.registry = CheckRegistry()
        self.registry.register(CheckSpec("availability", "LANCTL", availability, 5, 1, True))
        self.registry.register(CheckSpec("ping", "LANCTL", ping, 5, 1, True))
        self.registry.register(CheckSpec("arp", "LANCTL", arp, 5, 1, True))
        self.registry.register(CheckSpec("port", "LANCTL", tcp_port, 5, 1, False))
        self.registry.register(CheckSpec("service", "LANCTL", service, 60, 1, False))
        self.registry.register(CheckSpec("deep", "LANCTL", deep, 300, 1, False))
        self.session_manager = SessionManager(self.session_repo)
        self.incidents = IncidentManager(self.incident_repo)
        self.scheduler = None
        self.evaluator = None
        self.session = None
        self.profile = None
        self._scheduled: set[str] = set()
        self._check_specs = {}
        self._schedule_lock = threading.RLock()
        self._state_lock = threading.RLock()
        self._lifecycle_lock = threading.RLock()
        self._generation = object()
        self._accept_results = True
        self._session_registered = False
        self._requested_stop_status = None
        self._history_project = None
        self._stop_confirmed = True

    def start(self, session, profile_id=None, *, require_existing=False):
        with self._lifecycle_lock:
            if self.scheduler is not None or not self._stop_confirmed:
                from lanctl.shared.i18n import t

                raise RuntimeError(t("LANCTL.MONITOR.EXECUTION.ALREADY_RUNNING"))
            with self._state_lock:
                self._generation = object()
                self._accept_results = True
                self._session_registered = False
                self._requested_stop_status = None
            return self._start(session, profile_id, require_existing=require_existing)

    def _start(self, session, profile_id=None, *, require_existing=False):
        if profile_id is None:
            monitor = getattr(self.config, "monitor", lambda: None)()
            profile_id = getattr(monitor, "profile", "normal")
        profile = self.config.profile(profile_id or "normal")
        self.session_manager.activate(session, require_existing=require_existing)
        self.profile = profile
        self.session = session
        self._stop_confirmed = False
        settings = getattr(self.config, "config", {})
        self._history_project = settings.get("activeProject") or getattr(
            self.reports, "project", None
        )
        if not self._history_project and str(session.projectId).casefold().endswith(".vlf"):
            self._history_project = session.projectId
        self._scheduled.clear()
        self._check_specs.clear()
        self.evaluator = StateEvaluator(profile)
        self._restore_states()
        self.scheduler = MonitorScheduler(
            MonitorWorkerPool(profile.workers, max(profile.workers, profile.workers * 8)),
            self.clock,
            profile.jitter,
            error_handler=lambda task, error, failures, generation=self._generation, owner=session: (
                self._check_failed(task, error, failures, generation=generation, session=owner)
            ),
        )
        self._session_registered = True
        self._history(
            "monitor.started",
            session,
            "success",
            f"Monitor iniciado con perfil {profile.profile_id}",
        )
        self._schedule_targets(self._plans(session))
        if self.assignments and callable(getattr(self.assignments, "discover", None)):
            self._schedule_global(
                "monitor.network.discovery",
                "network",
                "discovery",
                profile.discovery_interval,
                profile.timeout,
                self._run_discovery,
                delay=min(10, profile.discovery_interval),
                execution_timeout=min(120, profile.discovery_interval),
            )
        if callable(getattr(self.metrics, "aggregate", None)):
            interval = max(300, min(profile.deep_interval, 3600))
            self._schedule_global(
                "monitor.storage.maintenance",
                "storage",
                "maintenance",
                interval,
                min(profile.timeout, 5),
                self._run_maintenance,
                delay=min(60, interval),
            )
        return session

    def _plans(self, session):
        if not self.assignments:
            return []
        provider = getattr(self.assignments, "plans", None)
        rows = provider(session) if callable(provider) else self.assignments.targets(session)
        plans = []
        for item in rows:
            plans.append(item if isinstance(item, MonitorTargetPlan) else MonitorTargetPlan(item))
        return plans

    def _schedule_targets(self, plans):
        for index, plan in enumerate(plans):
            target = plan.target
            if (
                not getattr(target, "device_id", "")
                or not getattr(target, "ip", "")
                or target.ip == "-"
            ):
                continue
            target_profile = (
                self.config.profile(plan.profile_id) if plan.profile_id else self.profile
            )
            presence_interval = self._priority_interval(target_profile, plan.priority)
            self._schedule_check(
                plan,
                "availability",
                presence_interval,
                target_profile.timeout,
                delay=min(index, presence_interval),
            )
            explicit = {str(item.get("type", "")).casefold() for item in plan.checks}
            if "service" not in explicit:
                self._schedule_check(
                    plan,
                    "service",
                    target_profile.services_interval,
                    target_profile.timeout,
                    {"workers": min(target_profile.workers, 4)},
                    delay=min(5 + index, target_profile.services_interval),
                )
            self._schedule_check(
                plan,
                "deep",
                target_profile.deep_interval,
                target_profile.timeout,
                {"workers": min(target_profile.workers, 4)},
                delay=min(30 + index * 2, target_profile.deep_interval),
            )
            for check in plan.checks:
                check_id = str(check.get("type", "")).casefold()
                spec = self.registry.get(check_id)
                interval = max(
                    spec.minimum_interval, parse_duration(check.get("interval", presence_interval))
                )
                timeout = float(check.get("timeout", target_profile.timeout))
                self._schedule_check(plan, check_id, interval, timeout, dict(check.get("args", {})))

    @staticmethod
    def _priority_interval(profile, priority):
        if priority == "critical":
            return profile.critical_interval
        if priority == "high":
            return min(profile.presence_interval, profile.critical_interval * 2)
        if priority == "low":
            return max(profile.presence_interval, profile.presence_interval * 2)
        return profile.presence_interval

    def _schedule_check(self, plan, check_id, interval, timeout, arguments=None, delay=0):
        task_id = f"monitor.{plan.target.device_id}.{check_id}"
        if arguments:
            suffix = arguments.get("port") or arguments.get("service")
            if suffix is not None:
                task_id += f".{suffix}"
        with self._schedule_lock:
            self._check_specs[task_id] = (check_id, plan.target, dict(arguments or {}))
            if task_id in self._scheduled:
                return
            self.registry.get(check_id)
            self._scheduled.add(task_id)
            self.scheduler.schedule(
                task_id,
                plan.target.device_id,
                check_id,
                interval,
                timeout,
                lambda _id, current_timeout, key=task_id, generation=self._generation, owner=self.session: (
                    self._run_scheduled_check(
                        key, current_timeout, generation=generation, session=owner
                    )
                ),
                delay=delay,
                execution_timeout=self._execution_timeout(check_id, timeout, arguments or {}),
            )

    @staticmethod
    def _execution_timeout(check_id, timeout, arguments):
        # Timeout remains the legacy per-probe numeric argument. Composite
        # checks also receive a capped whole-operation budget.
        if check_id == "availability":
            total = 2 * (timeout + 2)
        elif check_id in {"ping", "arp"}:
            total = timeout + 2
        elif check_id in {"deep", "service"} and "port" not in arguments:
            from math import ceil

            from lanctl.apps.ip.infrastructure.services.element_scanner import COMMON_PORTS

            workers = min(max(1, int(arguments.get("workers", 4))), 4)
            total = ceil(len(COMMON_PORTS) / workers) * 6 * timeout + 2 * timeout + 8
        else:
            total = timeout
        return min(120, max(timeout, total))

    def _current_execution(self, generation, session):
        if (
            not self._accept_results
            or generation is not self._generation
            or session is not self.session
        ):
            return False
        if self._session_registered:
            active = self.session_repo.active()
            return (
                active is not None
                and active.sessionId == session.sessionId
                and active.status == "active"
            )
        return True

    @contextmanager
    def _effect_guard(self, generation, session):
        with self._state_lock:
            if not self._current_execution(generation, session):
                yield False
                return
            database = getattr(self.metrics, "db", None)
            shared = database is not None and database is getattr(self.session_repo, "db", None)
            if shared:
                transaction = database.transaction()
            else:
                local = getattr(self.session_repo, "transaction", None)
                transaction = local() if callable(local) else nullcontext()
            with transaction:
                yield self._current_execution(generation, session)

    def _bind_budget(self, timeout, generation, session):
        if isinstance(timeout, CheckBudget):

            def authorized():
                with self._state_lock:
                    return self._current_execution(generation, session)

            timeout.authorized = authorized
            timeout.effects = lambda: self._effect_guard(generation, session)

    def _run_scheduled_check(self, task_id, timeout, *, generation=None, session=None):
        generation = self._generation if generation is None else generation
        session = self.session if session is None else session
        self._bind_budget(timeout, generation, session)
        with self._state_lock:
            if not self._current_execution(generation, session):
                return None
        with self._schedule_lock:
            specification = self._check_specs.get(task_id)
        if specification is None:
            return None
        check_id, target, arguments = specification
        return self._run_check(check_id, target, timeout, session, arguments, generation=generation)

    def _schedule_global(
        self,
        task_id,
        target,
        check_id,
        interval,
        timeout,
        handler,
        delay=0,
        *,
        execution_timeout=None,
    ):
        with self._schedule_lock:
            if task_id in self._scheduled:
                return
            self._scheduled.add(task_id)
            self.scheduler.schedule(
                task_id,
                target,
                check_id,
                interval,
                timeout,
                lambda current_target, budget, generation=self._generation, owner=self.session: (
                    handler(current_target, budget, generation=generation, session=owner)
                ),
                delay=delay,
                execution_timeout=execution_timeout,
            )

    def _execute_check(self, check_id, target, timeout, arguments):
        if check_id == "port":
            if "port" not in arguments:
                raise ValueError("el check port requiere args.port")
            return tcp_port(target, int(arguments["port"]), timeout)
        if check_id == "service":
            return service(
                target,
                timeout,
                name=str(arguments.get("service", "")),
                port=arguments.get("port"),
                workers=arguments.get("workers", 4),
            )
        if check_id == "deep":
            return deep(target, timeout, workers=arguments.get("workers", 4))
        return self.registry.get(check_id).handler(target, timeout)

    def _run_check(self, check_id, target, timeout, session, arguments=None, *, generation=None):
        generation = self._generation if generation is None else generation
        remaining_timeout(timeout)
        result = self._execute_check(check_id, target, timeout, arguments or {})
        remaining_timeout(timeout)
        with self._state_lock:
            previous = deepcopy(self.evaluator.states.get(result.target))
            try:
                with self._effect_guard(generation, session) as current:
                    if not current:
                        return None
                    remaining_timeout(timeout)
                    if isinstance(timeout, CheckBudget):
                        timeout.accepted = True
                    history = self._persist_check(check_id, result, session)
            except BaseException:
                if previous is None:
                    self.evaluator.states.pop(result.target, None)
                else:
                    self.evaluator.states[result.target] = previous
                raise
        for event in history:
            self._history(*event)
        return result

    def _persist_check(self, check_id, result, session):
        history = []
        self.metrics.write(result, session.sessionId)
        with self._state_lock:
            state, changed, before = self.evaluator.evaluate(result)
            database = getattr(self.metrics, "db", None)
            if database:
                transaction = getattr(database, "transaction", None)
                context = transaction() if callable(transaction) else database.connection
                with context:
                    database.execute(
                        "INSERT INTO device_state(device_id,presence,health,latency_ms,updated_at,session_id,consecutive_failures,consecutive_recoveries) VALUES(?,?,?,?,?,?,?,?) "
                        "ON CONFLICT(device_id) DO UPDATE SET presence=excluded.presence,health=excluded.health,latency_ms=excluded.latency_ms,updated_at=excluded.updated_at,session_id=excluded.session_id,consecutive_failures=excluded.consecutive_failures,consecutive_recoveries=excluded.consecutive_recoveries",
                        (
                            state.deviceId,
                            state.presence,
                            state.health,
                            result.latencyMs,
                            state.updatedAt,
                            session.sessionId,
                            state.consecutiveFailures,
                            state.consecutiveRecoveries,
                        ),
                    )
        error_cause = f"check.failed.{result.checkId}"
        if result.checkId not in {"availability", "ping", "arp"}:
            if result.success:
                self.incidents.resolve(state.deviceId, error_cause)
            else:
                self.incidents.open(
                    state.deviceId,
                    "warning",
                    error_cause,
                    "monitor.check",
                    session.runId,
                    session.sessionId,
                )
        self.incidents.resolve(state.deviceId, f"check.error.{check_id}")
        if changed:
            if state.presence == "offline":
                self.incidents.open(
                    state.deviceId,
                    "critical",
                    "device.offline",
                    "monitor.state.evaluate",
                    session.runId,
                    session.sessionId,
                )
                history.append(
                    ("device.offline", session, "error", f"{state.deviceId} está offline")
                )
            elif state.presence == "online":
                self.incidents.resolve(state.deviceId, "device.offline")
                event = "device.recovered" if before[0] == "offline" else "device.online"
                history.append((event, session, "success", f"{state.deviceId} está online"))
        return history

    def _check_failed(self, task, error, failures, *, generation=None, session=None):
        generation = self._generation if generation is None else generation
        session = self.session if session is None else session
        with self._effect_guard(generation, session) as current:
            if session is None or not current:
                return
            budget = getattr(task, "execution", None)
            if isinstance(budget, CheckBudget) and budget.cancelled.is_set():
                return
            history = self._persist_check_failure(task, error, failures, session)
        self._history(*history)

    def _persist_check_failure(self, task, error, failures, session):
        payload = {"type": type(error).__name__, "message": str(error)[:300], "failures": failures}
        self.metrics.write(
            CheckResult(task.check_id, task.target, False, error=payload), session.sessionId
        )
        self.incidents.open(
            task.target,
            "warning",
            f"check.error.{task.check_id}",
            "monitor.scheduler",
            session.runId,
            session.sessionId,
        )
        return (
            "monitor.check.failed",
            session,
            "error",
            f"Falló {task.check_id} para {task.target}: {payload['message']}",
        )

    def _run_discovery(self, _target, timeout, *, generation=None, session=None):
        generation = self._generation if generation is None else generation
        session = self.session if session is None else session
        self._bind_budget(timeout, generation, session)
        with self._state_lock:
            if not self._current_execution(generation, session):
                return None
        remaining_timeout(timeout)
        discovered = self.assignments.discover(session, timeout) or []
        remaining_timeout(timeout)
        plans = self._plans(session)
        remaining_timeout(timeout)
        active_ids = {plan.target.device_id for plan in plans if plan.target.ip not in ("", "-")}
        with self._effect_guard(generation, session) as current:
            if not current:
                return None
            remaining_timeout(timeout)
            with self._schedule_lock:
                for task_id, (_, target, _) in list(self._check_specs.items()):
                    if target.device_id not in active_ids:
                        self.scheduler.cancel(task_id)
                        self._scheduled.discard(task_id)
                        del self._check_specs[task_id]
                self._schedule_targets(plans)
            self.incidents.resolve("network", "check.error.discovery")
            if isinstance(timeout, CheckBudget):
                timeout.accepted = True
        self._history(
            "monitor.discovery.completed",
            session,
            "success",
            f"Descubrimiento completado: {len(discovered)} elementos",
        )
        return discovered

    def _run_maintenance(self, _target, timeout, *, generation=None, session=None):
        generation = self._generation if generation is None else generation
        session = self.session if session is None else session
        self._bind_budget(timeout, generation, session)
        with self._state_lock:
            if not self._current_execution(generation, session):
                return None
        remaining_timeout(timeout)
        options = (
            {"budget": timeout} if getattr(self.metrics, "cooperative_maintenance", False) else {}
        )
        aggregates = self.metrics.aggregate(**options)
        remaining_timeout(timeout)
        with self._state_lock:
            if not self._current_execution(generation, session):
                return None
        retention = getattr(self.config, "retention", dict)()
        deleted = (
            self.metrics.cleanup(retention, **options)
            if callable(getattr(self.metrics, "cleanup", None))
            else 0
        )
        remaining_timeout(timeout)
        with self._effect_guard(generation, session) as current:
            if not current:
                return None
            remaining_timeout(timeout)
            self.incidents.resolve("storage", "check.error.maintenance")
            if isinstance(timeout, CheckBudget):
                timeout.accepted = True
        return {"aggregates": aggregates, "deleted": deleted}

    def _restore_states(self):
        database = getattr(self.metrics, "db", None)
        if not database:
            return
        for row in database.execute("SELECT * FROM device_state"):
            self.evaluator.states[row["device_id"]] = DeviceState(
                row["device_id"],
                row["presence"],
                row["health"],
                row["consecutive_failures"],
                row["consecutive_recoveries"],
                row["updated_at"],
            )

    def cycle(self):
        with self._lifecycle_lock:
            if not self.scheduler:
                return 0
            if not self._current_execution(self._generation, self.session):
                with suppress(MonitorShutdownPending):
                    self.stop(self._requested_stop_status or "cancelled")
                return 0
            expired = self.session_manager.expire(mark=False)
            if expired:
                # Session remains explicitly stopping and owns its work on timeout.
                with suppress(MonitorShutdownPending):
                    self.stop("expired")
                return 0
            scheduler = self.scheduler
        return scheduler.tick()

    def foreground(self, poll=0.2, stop_event=None):
        while not (stop_event and stop_event.is_set()):
            self.cycle()
            with self._lifecycle_lock:
                if self._stop_confirmed:
                    break
            time.sleep(poll)

    @staticmethod
    def _stop_state_failed(error):
        from lanctl.core.errors import errors

        errors.from_exception(
            error,
            origin="LANCTL.Monitor.Service.StopState",
            code="MONITOR.STOP.STATE_FAILED",
            level=43,
            print_output=False,
        )

    def stop(self, status="completed", *, timeout=5.0):
        with self._lifecycle_lock:
            if self._requested_stop_status is None:
                self._requested_stop_status = status
            status = self._requested_stop_status
            if self.scheduler:
                self.scheduler.cancel()
                state_error = None
                with self._state_lock:
                    self._accept_results = False
                    try:
                        with self.session_manager._transaction():
                            active = self.session_repo.active()
                            if (
                                self.session
                                and active
                                and active.sessionId == self.session.sessionId
                            ):
                                self.session.status = "stopping"
                                self.session_repo.save(self.session)
                    except Exception as error:  # noqa: BLE001 - drain before propagating adapter failures
                        state_error = error
                        self._stop_state_failed(error)
                try:
                    self.scheduler.close(timeout=timeout)
                except MonitorShutdownPending as error:
                    from lanctl.core.errors import errors

                    errors.from_exception(
                        error,
                        origin="LANCTL.Monitor.Service.Stop",
                        code="MONITOR.STOP.PENDING",
                        level=24,
                        print_output=False,
                        once_key=f"monitor.stop.pending:{self.session.sessionId if self.session else 'none'}",
                    )
                    if state_error is not None:
                        raise error from state_error
                    try:
                        with self.session_manager._transaction():
                            active = self.session_repo.active()
                            if (
                                self.session
                                and active
                                and active.sessionId == self.session.sessionId
                                and self.session.error is None
                            ):
                                self.session.error = {
                                    "type": "MonitorShutdownPending",
                                    "message": str(error),
                                }
                                self.session_repo.save(self.session)
                    except Exception as metadata_error:
                        self._stop_state_failed(metadata_error)
                        raise error from metadata_error
                    raise
                if state_error is not None:
                    # Work is drained, but keep the owner until its state save
                    # can be retried; a caller may now safely release resources.
                    raise state_error
                self.scheduler = None
            active = self.session_repo.active()
            if self.session and (active is None or active.sessionId != self.session.sessionId):
                self._stop_confirmed = True
                return None
            try:
                session = self.session_manager.stop(
                    status, expected_session_id=self.session.sessionId if self.session else None
                )
            except RuntimeError:
                self._stop_confirmed = True
                return None
            self._stop_confirmed = True
            if session.error and session.error.get("type") == "MonitorShutdownPending":
                session.error = None
                self.session_repo.save(session)
            self.reports.completed(session)
            if status == "expired":
                self._history("monitor.session.stopped", session, "success", "Sesión expirada")
            else:
                self._history("monitor.stopped", session, "success", "Monitor detenido")
            return session

    def _history(self, event_type, session, result, summary):
        # El registro histórico no forma parte de la transacción del monitor.
        if not self._history_project:
            return
        with suppress(ValueError, OSError):
            HistoryService(self._history_project).write(
                HistoryEvent(
                    event_type,
                    "lanctl.monitor",
                    "local",
                    result,
                    summary,
                    correlationId=session.runId,
                    runId=session.runId,
                    taskId="monitor.management",
                    operationId="monitor.history.write",
                    details={
                        "sessionId": session.sessionId,
                        "mode": session.mode,
                        "authority": session.authority,
                    },
                )
            )
