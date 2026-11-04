"""Cooperative check budgets compatible with legacy numeric timeout handlers."""

from __future__ import annotations

import threading
import time
from concurrent.futures import CancelledError
from contextlib import contextmanager

from lanctl.shared.i18n import t


class CheckDeadlineExceeded(TimeoutError):
    """An accepted check exhausted its complete queue/execution budget."""


class MonitorShutdownPending(TimeoutError):
    """Accepted work remains owned and must drain before closing its session."""


class CheckBudget(float):
    def __new__(cls, seconds, *, clock=time.monotonic, lifetime=None):
        value = super().__new__(cls, seconds)
        value.clock = clock
        value.deadline = clock() + float(seconds if lifetime is None else lifetime)
        value.cancelled = threading.Event()
        value.authorized = None
        value.accepted = False
        value.effects = None
        return value

    @property
    def remaining(self):
        return max(0.0, self.deadline - self.clock())

    def checkpoint(self):
        if self.authorized is not None and not self.authorized():
            self.cancel()
        if self.cancelled.is_set():
            raise CancelledError(t("LANCTL.MONITOR.EXECUTION.CANCELLED"))
        if self.remaining <= 0:
            raise CheckDeadlineExceeded(t("LANCTL.MONITOR.EXECUTION.DEADLINE"))
        return min(float(self), self.remaining)

    def cancel(self):
        self.cancelled.set()

    def wait(self, seconds):
        self.cancelled.wait(min(max(0, seconds), self.checkpoint()))
        self.checkpoint()


def remaining_timeout(timeout):
    """Legacy numeric callers remain valid; cooperative callers share a budget."""
    return timeout.checkpoint() if isinstance(timeout, CheckBudget) else timeout


def discovery_progress(timeout):
    if not isinstance(timeout, CheckBudget):
        return None
    from lanctl.core.progress import ScanProgress

    class BudgetProgress(ScanProgress):
        wait_for_workers = True

        def __init__(self):
            super().__init__(enabled=False)

        def phase(self, phase):
            timeout.checkpoint()

        def cancelled(self):
            return timeout.cancelled.is_set() or timeout.remaining <= 0

        def complete(self):
            timeout.checkpoint()

    return BudgetProgress()


@contextmanager
def execution_effects(timeout):
    """Keep an owner's session authorization valid through an accepted write."""
    if isinstance(timeout, CheckBudget) and timeout.effects is not None:
        with timeout.effects() as current:
            if not current:
                timeout.cancel()
            timeout.checkpoint()
            yield
    else:
        remaining_timeout(timeout)
        yield
