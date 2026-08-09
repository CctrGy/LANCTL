from __future__ import annotations

import heapq
import random
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field


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


class MonitorWorkerPool:
    def __init__(self, workers=8, max_pending=64, executor=None):
        if not 1 <= workers <= 64 or max_pending < workers:
            raise ValueError("límites de workers no válidos")
        self.executor = executor or ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="lanctl-monitor"
        )
        self.capacity = threading.BoundedSemaphore(max_pending)
        self.closed = False

    def submit(self, handler, *args, done=None):
        if self.closed or not self.capacity.acquire(False):
            return None
        future = self.executor.submit(handler, *args)

        def finished(item):
            self.capacity.release()
            if done:
                done(item)

        future.add_done_callback(finished)
        return future

    def close(self, wait=True):
        self.closed = True
        self.executor.shutdown(wait=wait, cancel_futures=True)


class MonitorScheduler:
    def __init__(self, pool, clock, jitter=0.1, rng=None, error_handler=None):
        self.pool = pool
        self.clock = clock
        self.jitter = max(0, min(float(jitter), 0.5))
        self.rng = rng or random.Random()
        self.error_handler = error_handler
        self.queue = []
        self.inflight = set()
        self.sequence = 0
        self.cancelled = False
        self.lock = threading.RLock()

    def schedule(self, task_id, target, check_id, interval, timeout, handler, delay=0):
        if interval < 1 or not 0.05 <= timeout <= 120:
            raise ValueError("cadencia o timeout no válidos")
        with self.lock:
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
            heapq.heappush(self.queue, task)
        return task

    def tick(self):
        dispatched = 0
        now = self.clock()
        with self.lock:
            while self.queue and self.queue[0].due <= now and not self.cancelled:
                task = heapq.heappop(self.queue)
                key = (task.check_id, task.target)
                if task.cancelled:
                    continue
                if key in self.inflight:
                    task.due = now + min(task.interval, 1)
                    heapq.heappush(self.queue, task)
                    continue
                self.inflight.add(key)
                future = self.pool.submit(
                    task.handler,
                    task.target,
                    task.timeout,
                    done=lambda f, t=task, k=key: self._done(t, k, f),
                )
                if future is None:
                    self.inflight.discard(key)
                    task.due = now + min(task.interval, 1)
                    heapq.heappush(self.queue, task)
                    break
                dispatched += 1
        return dispatched

    def _done(self, task, key, future):
        try:
            future.result()
            task.failures = 0
        except Exception as error:  # noqa: BLE001 - frontera de tareas y plugins
            task.failures += 1
            task.last_error = f"{type(error).__name__}: {error}"
            if self.error_handler:
                try:
                    self.error_handler(task, error, task.failures)
                # El gestor de errores es externo y no debe detener el planificador.
                except Exception as callback_error:  # noqa: BLE001
                    task.last_error += (
                        f"; callback: {type(callback_error).__name__}: {callback_error}"
                    )
        factor = min(8, 2**task.failures)
        spread = task.interval * self.jitter * (self.rng.random() * 2 - 1)
        task.due = self.clock() + max(5, task.interval * factor + spread)
        with self.lock:
            self.inflight.discard(key)
            if not self.cancelled and not task.cancelled:
                heapq.heappush(self.queue, task)

    def cancel(self, task_id=None):
        with self.lock:
            if task_id is None:
                self.cancelled = True
            for task in self.queue:
                if task_id is None or task.task_id == task_id:
                    task.cancelled = True

    def close(self):
        self.cancel()
        self.pool.close()
