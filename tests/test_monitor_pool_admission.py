"""Admission keeps its capacity and orders accepted work before shutdown."""

from concurrent.futures import Future, ThreadPoolExecutor
from threading import Event

import pytest

from lanctl.apps.monitor.scheduler import MonitorWorkerPool


class RejectOnceExecutor:
    def __init__(self):
        self.reject = True
        self.future = Future()

    def submit(self, handler, *args):
        if self.reject:
            self.reject = False
            raise RuntimeError("submission rejected")
        return self.future

    def shutdown(self, **kwargs):
        self.future.cancel()


def test_rejected_submission_releases_capacity_for_retry():
    executor = RejectOnceExecutor()
    pool = MonitorWorkerPool(1, 1, executor)
    try:
        with pytest.raises(RuntimeError, match="submission rejected"):
            pool.submit(lambda: None)
        assert pool.submit(lambda: None) is executor.future
        executor.future.set_result(None)
        assert pool.capacity.acquire(False)
        assert not pool.capacity.acquire(False)
        pool.capacity.release()
    finally:
        pool.close()


def test_shutdown_cannot_overtake_an_admitted_submission():
    entered, release, shutdown, closing = Event(), Event(), Event(), Event()
    future = Future()

    class BlockingExecutor:
        def submit(self, handler, *args):
            entered.set()
            if not release.wait(5):
                raise TimeoutError("test did not release submission")
            if shutdown.is_set():
                raise RuntimeError("shutdown overtook submission")
            return future

        def shutdown(self, **kwargs):
            shutdown.set()
            future.cancel()

    pool = MonitorWorkerPool(1, 1, BlockingExecutor())

    def close():
        closing.set()
        pool.close()

    with ThreadPoolExecutor(max_workers=2) as threads:
        submission = threads.submit(pool.submit, lambda: None)
        assert entered.wait(5)
        closure = threads.submit(close)
        try:
            assert closing.wait(5)
            assert not shutdown.wait(0.1)
        finally:
            release.set()
        assert submission.result(timeout=5) is future
        closure.result(timeout=5)
    assert pool.closed and shutdown.is_set()
    assert pool.submit(lambda: None) is None
    assert pool.capacity.acquire(False)
    assert not pool.capacity.acquire(False)
    pool.capacity.release()


def test_callback_can_close_pool_without_admission_lock_deadlock():
    pool = MonitorWorkerPool(1, 1)
    done = Event()

    def callback(future):
        pool.close(wait=False)
        done.set()

    try:
        future = pool.submit(lambda: 42, done=callback)
        assert future.result(timeout=5) == 42
        assert done.wait(5)
    finally:
        pool.close()
