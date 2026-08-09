from __future__ import annotations

import threading
import time
from contextlib import suppress

from app.core.history import HistoryEvent, HistoryService

from .checks import CheckRegistry, arp, availability, deep, ping, service, tcp_port
from .configuration import parse_duration
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
        self._schedule_lock = threading.RLock()
        self._state_lock = threading.RLock()

    def start(self, session, profile_id=None):
        if profile_id is None:
            monitor = getattr(self.config, "monitor", lambda: None)()
            profile_id = getattr(monitor, "profile", "normal")
        profile = self.config.profile(profile_id or "normal")
        self.profile = profile
        self.session = session
        self.evaluator = StateEvaluator(profile)
        self._restore_states()
        self.scheduler = MonitorScheduler(
            MonitorWorkerPool(profile.workers, max(profile.workers, profile.workers * 8)),
            self.clock,
            profile.jitter,
            error_handler=self._check_failed,
        )
        session.status = "active"
        self.session_repo.save(session)
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
                lambda _id, current_timeout, p=plan, c=check_id, a=arguments or {}: self._run_check(
                    c, p.target, current_timeout, self.session, a
                ),
                delay=delay,
            )

    def _schedule_global(self, task_id, target, check_id, interval, timeout, handler, delay=0):
        with self._schedule_lock:
            if task_id in self._scheduled:
                return
            self._scheduled.add(task_id)
            self.scheduler.schedule(
                task_id, target, check_id, interval, timeout, handler, delay=delay
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

    def _run_check(self, check_id, target, timeout, session, arguments=None):
        result = self._execute_check(check_id, target, timeout, arguments or {})
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
                self._history("device.offline", session, "error", f"{state.deviceId} está offline")
            elif state.presence == "online":
                self.incidents.resolve(state.deviceId, "device.offline")
                event = "device.recovered" if before[0] == "offline" else "device.online"
                self._history(event, session, "success", f"{state.deviceId} está online")
        return result

    def _check_failed(self, task, error, failures):
        if not self.session:
            return
        payload = {"type": type(error).__name__, "message": str(error)[:300], "failures": failures}
        self.metrics.write(
            CheckResult(task.check_id, task.target, False, error=payload), self.session.sessionId
        )
        self.incidents.open(
            task.target,
            "warning",
            f"check.error.{task.check_id}",
            "monitor.scheduler",
            self.session.runId,
            self.session.sessionId,
        )
        self._history(
            "monitor.check.failed",
            self.session,
            "error",
            f"Falló {task.check_id} para {task.target}: {payload['message']}",
        )

    def _run_discovery(self, _target, timeout):
        discovered = self.assignments.discover(self.session, timeout) or []
        self._schedule_targets(self._plans(self.session))
        self.incidents.resolve("network", "check.error.discovery")
        self._history(
            "monitor.discovery.completed",
            self.session,
            "success",
            f"Descubrimiento completado: {len(discovered)} elementos",
        )
        return discovered

    def _run_maintenance(self, _target, _timeout):
        aggregates = self.metrics.aggregate()
        retention = getattr(self.config, "retention", dict)()
        deleted = (
            self.metrics.cleanup(retention)
            if callable(getattr(self.metrics, "cleanup", None))
            else 0
        )
        self.incidents.resolve("storage", "check.error.maintenance")
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
        if not self.scheduler:
            return 0
        expired = self.session_manager.expire()
        if expired:
            self.scheduler.close()
            self.scheduler = None
            self.reports.completed(expired)
            self._history("monitor.session.stopped", expired, "success", "Sesión expirada")
            return 0
        return self.scheduler.tick()

    def foreground(self, poll=0.2, stop_event=None):
        while not (stop_event and stop_event.is_set()):
            self.cycle()
            time.sleep(poll)

    def stop(self, status="completed"):
        if self.scheduler:
            self.scheduler.close()
            self.scheduler = None
        try:
            session = self.session_manager.stop(status)
        except RuntimeError:
            return None
        self.reports.completed(session)
        self._history("monitor.stopped", session, "success", "Monitor detenido")
        return session

    def _history(self, event_type, session, result, summary):
        # El registro histórico no forma parte de la transacción del monitor.
        with suppress(ValueError, OSError):
            HistoryService().write(
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
