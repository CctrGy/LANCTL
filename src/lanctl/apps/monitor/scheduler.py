from __future__ import annotations

import heapq
import random
import threading
import time
from concurrent.futures import CancelledError, ThreadPoolExecutor
from dataclasses import dataclass, field

from lanctl.shared.i18n import t

from .execution import CheckBudget, MonitorShutdownPending


@dataclass(order=True)
class ScheduledCheck:
    due: float
    sequence: int
    task_id: str = field(compare=False)
    target: str = field(compare=False)
    check_id: str = field(compare=False)
    interval: float = field(compare=False)
    timeout: float = field(compare=False)
    handler: object = field(compare=False)
    failures: int = field(default=0, compare=False)
    cancelled: bool = field(default=False, compare=False)
    last_error: str = field(default="", compare=False)
    execution: CheckBudget | None = field(default=None, compare=False, repr=False)
    execution_timeout: float | None = field(default=None, compare=False)


class MonitorWorkerPool:
    def __init__(self, workers=8, max_pending=64, executor=None):
        if not 1 <= workers <= 64 or max_pending < workers:
            raise ValueError("límites de workers no válidos")
        self.executor = executor or ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="lanctl-monitor"
        )
        self.capacity = threading.BoundedSemaphore(max_pending)
        self.closed = False
        self._submission_lock = threading.RLock()
        self._condition = threading.Condition(self._submission_lock)
        self._futures = set()
        self._shutdown_started = False

    def submit(self, handler, *args, done=None):
        with self._submission_lock:
            if self.closed or not self.capacity.acquire(False):
                return None
            try:
                future = self.executor.submit(handler, *args)
            except BaseException:
                # A rejected submission owns no future/callback to release it.
                self.capacity.release()
                raise
            self._futures.add(future)

        def finished(item):
            try:
                if done:
                    done(item)
            finally:
                with self._condition:
                    self._futures.discard(item)
                    self.capacity.release()
                    self._condition.notify_all()

        future.add_done_callback(finished)
        return future

    @property
    def quiescent(self):
        with self._submission_lock:
            return not self._futures

    def close(self, wait=True, *, timeout=5.0):
        with self._submission_lock:
            self.closed = True
            start_shutdown = not self._shutdown_started
            self._shutdown_started = True
        if start_shutdown:
            try:
                self.executor.shutdown(wait=False, cancel_futures=True)
            except BaseException:
                with self._submission_lock:
                    self._shutdown_started = False
                raise
        if not wait:
            return self.quiescent
        deadline = None if timeout is None else time.monotonic() + max(0, timeout)
        with self._condition:
            while self._futures:
                remaining = None if deadline is None else deadline - time.monotonic()
                if remaining is not None and remaining <= 0:
                    raise MonitorShutdownPending(
                        t("LANCTL.MONITOR.EXECUTION.SHUTDOWN_PENDING", count=len(self._futures))
                    )
                self._condition.wait(remaining)
        self.executor.shutdown(wait=True, cancel_futures=True)
        return True


class MonitorScheduler:
    def __init__(self, pool, clock, jitter=0.1, rng=None, error_handler=None):
        self.pool = pool
        self.clock = clock
        self.jitter = max(0, min(float(jitter), 0.5))
        self.rng = rng or random.Random()
        self.error_handler = error_handler
        self.queue = []
        self.tasks = {}
        self.inflight = set()
        self.sequence = 0
        self.cancelled = False
        self.lock = threading.RLock()

    def schedule(
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
        if interval < 1 or not 0.05 <= timeout <= 120:
            raise ValueError("cadencia o timeout no válidos")
        if execution_timeout is not None and not 0.05 <= execution_timeout <= 120:
            raise ValueError(t("LANCTL.MONITOR.EXECUTION.INVALID_BUDGET"))
        with self.lock:
            previous = self.tasks.get(task_id)
            if previous is not None:
                previous.cancelled = True
                if previous.execution is not None:
                    previous.execution.cancel()
            self.sequence += 1
            task = ScheduledCheck(
                self.clock() + max(0, delay),
                self.sequence,
                task_id,
                target,
                check_id,
                interval,
                timeout,
                handler,
            )
            task.execution_timeout = execution_timeout
            self.tasks[task_id] = task
            heapq.heappush(self.queue, task)
        return task

    def tick(self):
        dispatched = 0
        now = self.clock()
        while True:
            with self.lock:
                if self.cancelled or not self.queue or self.queue[0].due > now:
                    break
                task = heapq.heappop(self.queue)
                key = (task.check_id, task.target)
                if task.cancelled:
                    continue
                if key in self.inflight:
                    task.due = now + min(task.interval, 1)
                    heapq.heappush(self.queue, task)
                    continue
                self.inflight.add(key)
                budget = CheckBudget(
                    task.timeout, clock=self.clock, lifetime=task.execution_timeout
                )
                task.execution = budget
            # A Future may synchronously deliver its callback from submit.
            # Never call a handler or external callback under the queue lock.
            try:
                future = self.pool.submit(
                    self._execute,
                    task,
                    budget,
                    done=lambda f, t=task, k=key: self._done(t, k, f),
                )
            except BaseException:
                with self.lock:
                    self.inflight.discard(key)
                    budget.cancel()
                    if (
                        not self.cancelled
                        and not task.cancelled
                        and self.tasks.get(task.task_id) is task
                    ):
                        task.due = self.clock() + min(task.interval, 1)
                        heapq.heappush(self.queue, task)
                raise
            if future is None:
                with self.lock:
                    self.inflight.discard(key)
                    budget.cancel()
                    if (
                        not self.cancelled
                        and not task.cancelled
                        and self.tasks.get(task.task_id) is task
                    ):
                        task.due = now + min(task.interval, 1)
                        heapq.heappush(self.queue, task)
                break
            dispatched += 1
        return dispatched

    @staticmethod
    def _execute(task, budget):
        budget.checkpoint()
        try:
            result = task.handler(task.target, budget)
        except Exception:
            if not budget.accepted:
                budget.checkpoint()
            raise
        if not budget.accepted:
            budget.checkpoint()
        return result

    def _done(self, task, key, future):
        with self.lock:
            if self.cancelled or task.cancelled or self.tasks.get(task.task_id) is not task:
                self.inflight.discard(key)
                return
        # External callbacks must run without retaining the scheduler lock.
        self._complete_current(task, key, future)

    def _complete_current(self, task, key, future):
        try:
            future.result()
            task.failures = 0
        except CancelledError:
            with self.lock:
                self.inflight.discard(key)
                if self.tasks.get(task.task_id) is task:
                    self.tasks.pop(task.task_id, None)
                task.cancelled = True
            return
        except Exception as error:  # noqa: BLE001 - frontera de tareas y plugins
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.Monitor.Scheduler.Task",
                code="MONITOR.TASK.RETRY",
                level=18,
                details={"taskId": task.task_id, "failures": task.failures + 1},
                print_output=False,
            )
            task.failures += 1
            task.last_error = f"{type(error).__name__}: {error}"
            if self.error_handler:
                try:
                    self.error_handler(task, error, task.failures)
                # El gestor de errores es externo y no debe detener el planificador.
                except Exception as callback_error:  # noqa: BLE001
                    errors.from_exception(
                        callback_error,
                        origin="LANCTL.Monitor.Scheduler.ErrorCallback",
                        code="MONITOR.ERROR_CALLBACK.IGNORED",
                        level=16,
                        details={"taskId": task.task_id},
                        print_output=False,
                    )
                    task.last_error += (
                        f"; callback: {type(callback_error).__name__}: {callback_error}"
                    )
        factor = min(8, 2**task.failures)
        spread = task.interval * self.jitter * (self.rng.random() * 2 - 1)
        task.due = self.clock() + max(5, task.interval * factor + spread)
        with self.lock:
            self.inflight.discard(key)
            if not self.cancelled and not task.cancelled and self.tasks.get(task.task_id) is task:
                heapq.heappush(self.queue, task)

    def cancel(self, task_id=None):
        with self.lock:
            if task_id is None:
                self.cancelled = True
            for task in list(self.tasks.values()):
                if task_id is None or task.task_id == task_id:
                    task.cancelled = True
                    if task.execution is not None:
                        task.execution.cancel()
                    self.tasks.pop(task.task_id, None)

    def close(self, *, timeout=5.0):
        self.cancel()
        return self.pool.close(timeout=timeout)
