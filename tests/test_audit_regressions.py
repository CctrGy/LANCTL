"""Regresiones de la auditoría técnica de octubre de 2026."""

import multiprocessing
import os
import time
from pathlib import Path

import pytest

from lanctl.core.plugins.isolated_runtime import (
    IsolatedPluginRuntime,
    _receive_message,
)


class _PickleMarker:
    def __init__(self, path):
        self.path = path

    def __reduce__(self):
        return Path.touch, (self.path,)


def test_isolated_ipc_never_unpickles_child_objects(tmp_path):
    receiver, sender = multiprocessing.Pipe()
    marker = tmp_path / "must-not-exist"
    try:
        sender.send(_PickleMarker(marker))
        with pytest.raises(ValueError, match="IPC"):
            _receive_message(receiver)
        assert not marker.exists()
    finally:
        sender.close()
        receiver.close()


@pytest.mark.parametrize(
    "payload",
    [b"[]", b"{}", b'["CALL","log",[]]', b'["READY",true]', b"x" * 65537],
    ids=["empty", "object", "arguments", "pid", "oversized"],
)
def test_isolated_ipc_rejects_invalid_or_oversized_frames(payload):
    class Connection:
        def recv_bytes(self, maxlength):
            if len(payload) > maxlength:
                raise OSError("bad message length")
            return payload

    with pytest.raises((ValueError, OSError)):
        _receive_message(Connection())


def test_isolated_runtime_rejects_pickle_from_real_plugin(tmp_path):
    entry = tmp_path / "main.exec"
    entry.write_text(
        "import os\n"
        "class Payload:\n"
        "    def __reduce__(self):\n"
        "        return os.getpid, ()\n"
        "def activate(api):\n"
        "    api.connection.send(('CALL', 'log', (Payload(),)))\n",
        encoding="utf-8",
    )
    events = []
    runtime = IsolatedPluginRuntime("audit.ipc", entry, audit=lambda *args: events.append(args))
    try:
        with pytest.raises(ValueError, match="IPC"):
            runtime.start()
        assert not any(str(os.getpid()) in event for event in events)
    finally:
        runtime.stop()


def test_isolated_parent_enforces_budget_even_if_plugin_bypasses_api(tmp_path):
    entry = tmp_path / "main.exec"
    entry.write_text(
        "def activate(api):\n"
        "    for _ in range(2):\n"
        '        api.connection.send_bytes(b\'["CALL","log",["hello"]]\')\n',
        encoding="utf-8",
    )
    runtime = IsolatedPluginRuntime("audit.budget", entry, max_calls=1)
    try:
        with pytest.raises(RuntimeError, match="límite de llamadas"):
            runtime.start()
    finally:
        runtime.stop()


def test_isolated_stop_never_unpickles_deactivation_message(tmp_path):
    marker = tmp_path / "must-not-exist"
    entry = tmp_path / "main.exec"
    entry.write_text(
        "from pathlib import Path\n"
        "class Payload:\n"
        "    def __reduce__(self):\n"
        f"        return Path.touch, (Path({str(marker)!r}),)\n"
        "def activate(api):\n"
        "    global connection\n"
        "    connection = api.connection\n"
        "def deactivate():\n"
        "    connection.send(Payload())\n",
        encoding="utf-8",
    )
    runtime = IsolatedPluginRuntime("audit.stop", entry)
    try:
        runtime.start()
    finally:
        runtime.stop()
    assert not marker.exists()


@pytest.mark.skipif(os.name == "nt", reason="framing parcial de pipes POSIX")
def test_partial_ipc_frame_cannot_bypass_activation_timeout(tmp_path):
    entry = tmp_path / "main.exec"
    entry.write_text(
        "import os, struct, time\n"
        "def activate(api):\n"
        "    os.write(api.connection.fileno(), struct.pack('!i', 100) + b'[')\n"
        "    time.sleep(30)\n",
        encoding="utf-8",
    )
    runtime = IsolatedPluginRuntime("audit.partial", entry, timeout=0.1)
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError):
            runtime.start()
        assert time.monotonic() - start < 10
    finally:
        runtime.stop()
