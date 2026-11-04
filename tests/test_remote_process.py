"""Actual subprocesses with bounded allocations, output and cleanup."""

import subprocess
import sys
import tracemalloc
from concurrent.futures import CancelledError, ThreadPoolExecutor
from pathlib import Path
from threading import Event, Timer
from types import SimpleNamespace

import pytest

from lanctl.apps.access.remote_process import bounded_run


def test_large_simultaneous_streams_are_drained_with_shared_limit():
    command = [
        sys.executable,
        "-c",
        "import os; chunk=b'x'*8192; [(os.write(1,chunk),os.write(2,chunk)) for _ in range(1024)]",
    ]
    result = bounded_run(command, timeout=10, max_output=65536)
    assert result.returncode == 0
    assert result.truncated
    assert len((result.stdout + result.stderr).encode()) == 65536


def test_small_output_preserves_streams_and_exit_status():
    result = bounded_run(
        [sys.executable, "-c", "import os; os.write(1,b'out'); os.write(2,b'err'); exit(7)"],
        timeout=5,
    )
    assert (result.returncode, result.stdout, result.stderr, result.truncated) == (
        7,
        "out",
        "err",
        False,
    )


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("payload", ["b'\\xff'*4096", "'🙂'.encode()*4096"])
def test_adapter_final_utf8_response_includes_marker_inside_limit(
    monkeypatch, tmp_path, language, payload
):
    from lanctl.apps.access import remote
    from lanctl.shared import i18n

    manager = i18n.LanguageManager(tmp_path / "languages")
    manager.install(Path(__file__).resolve().parents[1] / "bundled/languages/spanish.lang")
    monkeypatch.setattr(i18n, "_MANAGER", manager)
    monkeypatch.setattr(remote, "MAX_OUTPUT", 128)
    adapter = remote.LanctlCommandAdapter(SimpleNamespace(require=lambda *args: None))
    monkeypatch.setattr(
        adapter, "command", lambda args: [sys.executable, "-c", f"import os; os.write(1,{payload})"]
    )
    with i18n.language_context(language):
        code, output = adapter.execute(None, "search device")
    assert code == 0
    assert len(output.encode("utf-8")) <= 128
    assert output.endswith("[Salida truncada]" if language == "es" else "[Output truncated]")


@pytest.mark.parametrize("cancel", [False, True])
def test_timeout_and_cancellation_reap_child(monkeypatch, cancel):
    from lanctl.apps.access import remote_process

    children = []
    timers = []
    event = Event()
    popen = subprocess.Popen

    def spawn(*args, **kwargs):
        child = popen(*args, **kwargs)
        children.append(child)
        if cancel:
            timer = Timer(0.05, event.set)
            timers.append(timer)
            timer.start()
        return child

    monkeypatch.setattr(remote_process.subprocess, "Popen", spawn)
    with pytest.raises(CancelledError if cancel else subprocess.TimeoutExpired):
        bounded_run(
            [sys.executable, "-c", "import time; time.sleep(60)"],
            timeout=0.1,
            cancel_event=event,
        )
    for timer in timers:
        timer.join(timeout=1)
        assert not timer.is_alive()
    assert len(children) == 1
    assert children[0].poll() is not None
    assert children[0].stdout.closed and children[0].stderr.closed


def test_two_large_captures_have_bounded_python_peak(record_property):
    command = [
        sys.executable,
        "-c",
        "import os; chunk=b'x'*16384; [(os.write(1,chunk),os.write(2,chunk)) for _ in range(2048)]",
    ]
    limit = 1024 * 1024
    tracemalloc.start()
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: bounded_run(command, timeout=30), range(2)))
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    record_property("capture_python_peak_bytes", peak)
    record_property("emitted_bytes", 128 * limit)
    print(f"capture_python_peak_bytes={peak}; emitted_bytes={128 * limit}; concurrent=2")
    assert peak < 16 * limit
    assert all(result.returncode == 0 and result.truncated for result in results)
    assert all(len((result.stdout + result.stderr).encode()) == limit for result in results)


@pytest.mark.skipif(sys.platform != "linux", reason="Linux process-group cleanup evidence")
def test_timeout_cleans_descendant_that_keeps_pipes_open(tmp_path):
    import time

    pidfile = tmp_path / "child.pid"
    script = (
        "import os,time,pathlib; child=os.fork(); "
        f"pathlib.Path({str(pidfile)!r}).write_text(str(child)) if child else None; "
        "time.sleep(60) if child == 0 else None"
    )
    with pytest.raises(subprocess.TimeoutExpired):
        bounded_run([sys.executable, "-c", script], timeout=0.5)
    descendant = int(pidfile.read_text())
    assert descendant > 0
    status = Path(f"/proc/{descendant}/stat")
    deadline = time.monotonic() + 2
    while status.exists() and time.monotonic() < deadline:
        if status.read_text().split()[2] == "Z":
            break
        time.sleep(0.01)
    assert not status.exists() or status.read_text().split()[2] == "Z"
