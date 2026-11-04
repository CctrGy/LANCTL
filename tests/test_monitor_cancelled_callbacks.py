"""Late Future callbacks must not report failures for obsolete tasks."""

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event

import pytest

from lanctl.apps.monitor.scheduler import MonitorScheduler, MonitorWorkerPool


class DeferredExecutor:
    def __init__(self):
        self.future = Future()

    def submit(self, handler, *args):
        return self.future

    def shutdown(self, **kwargs):
        self.future.cancel()


@pytest.mark.parametrize("action", ["cancel-one", "cancel-all", "replace"])
def test_obsolete_failure_does_not_reach_error_callback(action):
    executor = DeferredExecutor()
    reported = []
    scheduler = MonitorScheduler(
        MonitorWorkerPool(1, 1, executor),
        lambda: 0,
        error_handler=lambda *args: reported.append(args),
    )
    old = scheduler.schedule("task", "device", "ping", 5, 0.1, lambda *args: None)
    assert scheduler.tick() == 1
    if action == "replace":
        scheduler.schedule("task", "device", "ping", 10, 0.1, lambda *args: None)
    else:
        scheduler.cancel("task" if action == "cancel-one" else None)
    executor.future.set_exception(OSError("obsolete failure"))
    assert reported == []
    assert old.failures == 0
    assert not scheduler.inflight
    assert all(task is not old for task in scheduler.queue)
    scheduler.close()


def test_error_callback_can_request_cancellation_from_another_thread():
    executor = DeferredExecutor()
    cancelled = Event()

    def report(*args):
        with ThreadPoolExecutor(max_workers=1) as threads:
            threads.submit(scheduler.cancel).result(timeout=2)
        cancelled.set()

    scheduler = MonitorScheduler(MonitorWorkerPool(1, 1, executor), lambda: 0, error_handler=report)
    scheduler.schedule("task", "device", "ping", 5, 0.1, lambda *args: None)
    scheduler.tick()
    executor.future.set_exception(OSError("current failure"))
    assert cancelled.wait(2)
    assert scheduler.cancelled
    assert not scheduler.inflight
    assert scheduler.tick() == 0
    scheduler.close()
