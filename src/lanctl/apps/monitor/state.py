from __future__ import annotations

from .models import CheckResult, DeviceState, MonitorProfile, now_iso


class StateEvaluator:
    def __init__(self, profile: MonitorProfile):
        self.profile = profile
        self.states = {}
        self.check_health = {}

    def evaluate(self, result: CheckResult):
        state = self.states.setdefault(result.target, DeviceState(result.target))
        before = (state.presence, state.health)
        if result.checkId in {"availability", "ping", "arp"}:
            if result.success:
                state.consecutiveRecoveries += 1
                state.consecutiveFailures = 0
                if state.consecutiveRecoveries >= self.profile.recovery_threshold:
                    state.presence = "online"
            else:
                state.consecutiveFailures += 1
                state.consecutiveRecoveries = 0
                if state.consecutiveFailures >= self.profile.failure_threshold:
                    state.presence = "offline"
        latency = result.latencyMs
        health = "warning" if not result.success else "healthy"
        if latency is not None:
            health = "critical" if latency >= 1000 else "warning" if latency >= 250 else health
        checks = self.check_health.setdefault(result.target, {})
        checks[(result.checkId, result.metrics.get("service"), result.metrics.get("port"))] = health
        if state.health != "maintenance":
            severity = {"healthy": 0, "warning": 1, "critical": 2}
            state.health = max(checks.values(), key=severity.__getitem__)
        state.updatedAt = now_iso()
        return state, before != (state.presence, state.health), before
