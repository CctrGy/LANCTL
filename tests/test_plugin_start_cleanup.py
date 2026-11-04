"""Fault injection proves startup ownership without exhausting host memory."""

import json
import multiprocessing
import sys
import threading
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.core.plugins import isolated_runtime


@pytest.mark.parametrize("failed_thread", ["LANCTL plugin IPC", "LANCTL plugin watchdog"])
def test_thread_admission_failure_reaps_started_worker(tmp_path, monkeypatch, failed_thread):
    entry = tmp_path / "main.exec"
    entry.write_text("def activate(api): pass\n")
    processes = []
    context = multiprocessing.get_context("spawn")
    process_class = context.Process

    def create_process(*args, **kwargs):
        process = process_class(*args, **kwargs)
        processes.append(process)
        return process

    start = threading.Thread.start

    def start_thread(thread):
        if thread.name.startswith(failed_thread):
            raise RuntimeError("synthetic-thread-admission")
        return start(thread)

    monkeypatch.setattr(context, "Process", create_process)
    monkeypatch.setattr(threading.Thread, "start", start_thread)
    runtime = isolated_runtime.IsolatedPluginRuntime("test.cleanup", entry)
    try:
        with pytest.raises(RuntimeError, match="synthetic-thread-admission"):
            runtime.start()
        assert processes and all(not process.is_alive() for process in processes)
        assert runtime.process is None and runtime._connection is None and runtime._reader is None
        assert runtime._watchdog_thread is None
        assert runtime not in isolated_runtime._RUNTIMES
    finally:
        runtime.stop()


def test_worker_reports_parent_watcher_start_failure_before_activation(monkeypatch, tmp_path):
    messages = []

    class Connection:
        closed = False

        def send_bytes(self, payload):
            messages.append(json.loads(payload))

        def close(self):
            self.closed = True

    def fail():
        raise RuntimeError("synthetic-watcher-admission")

    monkeypatch.setattr(isolated_runtime, "_apply_memory_limit", lambda value: None)
    monkeypatch.setattr(isolated_runtime, "_watch_parent", fail)
    connection = Connection()
    isolated_runtime._worker(connection, "test.cleanup", str(tmp_path / "unused"), 128, 1000)
    assert messages == [["ERROR", "RuntimeError", "synthetic-watcher-admission"]]
    assert connection.closed


@pytest.mark.skipif(sys.platform != "linux", reason="Linux allocator and RLIMIT_AS contract")
@pytest.mark.parametrize("supported", [False, True])
def test_worker_allocator_does_not_relax_manifest_memory_limit(monkeypatch, supported):
    import resource

    mallopt = Mock(return_value=1)
    library = SimpleNamespace(mallopt=mallopt) if supported else SimpleNamespace()
    monkeypatch.setattr(isolated_runtime.ctypes, "CDLL", lambda name: library)
    limits = []
    monkeypatch.setattr(resource, "setrlimit", lambda kind, value: limits.append((kind, value)))
    isolated_runtime._apply_memory_limit(128)
    assert limits == [(resource.RLIMIT_AS, (128 * 1024 * 1024, 128 * 1024 * 1024))]
    if supported:
        mallopt.assert_called_once_with(-8, 1)
    else:
        mallopt.assert_not_called()
