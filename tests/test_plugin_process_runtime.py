"""Real processes: permissions, generation revocation and bounded termination."""

import json
import multiprocessing
import os
import runpy
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import pytest

from lanctl.core.plugins.contracts import FunctionResult
from lanctl.core.plugins.isolated_runtime import IsolatedPluginRuntime
from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.models import PluginManifest
from lanctl.core.plugins.package import build_package
from lanctl.core.plugins.runtime_protocol import _decode, _encode, _receive


@pytest.fixture
def factory(tmp_path, monkeypatch):
    monkeypatch.setattr(PluginManager, "audit", Mock())
    manager = PluginManager(tmp_path / "installed", tmp_path / "registry.json")

    def create(
        code, *, plugin_id="test.process", permissions=(), depends=(), api_version=2, limits=None
    ):
        source = tmp_path / "sources" / plugin_id
        source.mkdir(parents=True)
        manifest = dict(
            schemaVersion=1,
            id=plugin_id,
            version="1.0.0",
            runtime="isolated",
            runtimeApiVersion=api_version,
            permissions=list(permissions),
            depends=list(depends),
            limits=limits or {},
        )
        (source / "plugin.info").write_text(json.dumps(manifest), encoding="utf-8")
        (source / "main.exec").write_text(code, encoding="utf-8")
        package = tmp_path / f"{plugin_id}.lcp"
        build_package(source, package)
        manager.install(package)
        return manager.enable(plugin_id, grant=set(permissions))

    yield manager, create
    manager.close()


FUNCTION = """
import os
import time
from lanctl.core.plugins.contracts import FunctionResult
def activate(api):
    def echo(value):
        api.log('echo', detail=str(value))
        return FunctionResult(True, data={'pid': os.getpid(), 'value': value, 'settings': api.settings})
    api.functions.register('Test.Process.Action.Echo', echo, FunctionResult)
"""


def test_real_process_callbacks_and_reload_reject_old_generation(factory):
    manager, create = factory
    plugin = create(FUNCTION, permissions=["functions.register"])
    process = plugin.isolated_runtime.process
    first = manager.runtime_status("test.process")
    retained = manager.functions._items["test.process.action.echo"][1]
    result = manager.functions.call("Test.Process.Action.Echo", {"a": [1, True, None]})
    assert isinstance(result, FunctionResult)
    assert result.data["pid"] != os.getpid()
    assert result.data["value"] == {"a": [1, True, None]}
    manager.reload("test.process")
    assert not process.is_alive()
    assert manager.runtime_status("test.process")["generation"] != first["generation"]
    with pytest.raises(PermissionError):
        retained("stale")
    assert manager.functions.call("Test.Process.Action.Echo", "new").success


def test_inventory_projection_and_extension_return_are_transportable(
    factory, tmp_path, monkeypatch
):
    from lanctl.core import config
    from lanctl.core.database import DeviceDatabase

    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    settings = config.load_config()
    settings["database"] = str(tmp_path / "devices.json")
    config.save_config(settings)
    DeviceDatabase(settings["database"]).upsert([{"MAC": "02:00:00:00:00:10", "IP": "192.0.2.10"}])
    manager, create = factory
    create(
        """
from lanctl.core.plugins.contracts import FunctionResult
def activate(api):
    extension = api.extensions.register('Test.Process.Panel.Inventory', 'ui-panel', {'title': 'Test'})
    def read():
        return FunctionResult(True, data={'owner': extension.owner, 'devices': api.inventory.list()})
    api.functions.register('Test.Process.Action.Read', read, FunctionResult)
""",
        permissions=["functions.register", "inventory.read", "ui-panel.register"],
    )
    result = manager.functions.call("Test.Process.Action.Read")
    assert result.data["owner"] == "test.process"
    assert result.data["devices"][0]["IP"] == "192.0.2.10"
    manager.revoke("test.process")
    assert not manager.extensions.list("ui-panel")


def test_revocation_interrupts_callback_and_native_threads(factory):
    manager, create = factory
    entered = threading.Event()
    original_audit = manager.audit

    def audit(*args):
        if args[1] == "entered":
            entered.set()
        original_audit(*args)

    manager.audit = audit
    plugin = create(
        """
import time, threading
from lanctl.core.plugins.contracts import FunctionResult
def spin():
    while True:
        time.sleep(.01)
def activate(api):
    threading.Thread(target=spin, daemon=False).start()
    def hang():
        api.log('entered')
        spin()
    api.functions.register('Test.Process.Action.Hang', hang, FunctionResult)
def deactivate():
    spin()
""",
        permissions=["functions.register"],
        limits={"timeoutSeconds": 30},
    )
    process = plugin.isolated_runtime.process
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(manager.functions.call, "Test.Process.Action.Hang")
        assert entered.wait(5)
        started = time.monotonic()
        manager.revoke("test.process")
        assert time.monotonic() - started < 4
        with pytest.raises((PermissionError, EOFError, OSError)):
            future.result(timeout=4)
    assert not process.is_alive()
    status = manager.runtime_status("test.process")
    assert status["terminationConfirmed"] and not status["cleanupPending"]
    assert not status["coreAccess"] and not status["restartRequired"]
    assert not manager.functions._items


def test_foreign_revocation_stops_dependent_processes_without_api_calls(factory):
    manager, create = factory
    first = create("def activate(api): pass\n")
    second = create("def activate(api): pass\n", plugin_id="test.child", depends=["test.process"])
    processes = [first.isolated_runtime.process, second.isolated_runtime.process]
    manager._authorization.start_watch()
    other = PluginManager(manager.root, manager.registry_path)
    other.revoke("test.process")
    deadline = time.monotonic() + 5
    while any(p.is_alive() for p in processes) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert all(not p.is_alive() for p in processes)
    assert not manager.runtime_status("test.child")["coreAccess"]


def test_event_callbacks_keep_core_contract_and_are_removed(factory):
    manager, create = factory
    create(
        """
from lanctl.core.plugins.events import HookDecision
def activate(api):
    def before(event):
        api.log('event', detail=event.metadata.event_id)
        return HookDecision(False, 'denied by plugin')
    api.events.subscribe('LANCTL.Network.Scan.BeforeStart', before)
""",
        permissions=["events.listen"],
    )
    values = dict(scan_id="test", target_range=None, running=False, active=False)
    _, decision = manager.events.emit("LANCTL.Network.Scan.BeforeStart", values)
    assert not decision.allowed
    retained = manager.events._subscriptions[("lanctl.network.scan.beforestart", 1)][0][2]
    manager.disable("test.process")
    with pytest.raises(PermissionError):
        retained(None)
    assert manager.events.emit("LANCTL.Network.Scan.BeforeStart", values)[1].allowed


@pytest.mark.parametrize(
    "code",
    [
        "api.functions.register('Test.Process.Action.X', lambda: None, FunctionResult)",
        "api._peer.request('inventory.list')",
        "api._peer.request('_manager.close')",
        "api._peer.request('functions.register', 'LANCTL.Core.Action.X', '1')",
    ],
)
def test_permission_checks_cannot_be_bypassed_by_rpc(factory, code):
    manager, create = factory
    with pytest.raises((PermissionError, RuntimeError), match=r"permiso|permitida|namespace"):
        create(
            "from lanctl.core.plugins.contracts import FunctionResult\ndef activate(api):\n    "
            + code
            + "\n"
        )
    assert not manager.functions._items
    assert not manager.runtime_status("test.process")["coreAccess"]


def test_runtime_failure_never_reports_cleanup_success_or_allows_new_generation(
    factory, monkeypatch
):
    manager, create = factory

    def settled_status():
        # Cleanup is asynchronous; disable may return its bounded wait before
        # the watcher-owned cleanup completes, especially under coverage.
        deadline = time.monotonic() + 5
        state = manager.runtime_status("test.process")
        while state["cleanupPending"] and time.monotonic() < deadline:
            time.sleep(0.01)
            state = manager.runtime_status("test.process")
        assert not state["cleanupPending"]
        return state

    plugin = create("def activate(api): pass\n")
    runtime = plugin.isolated_runtime
    process = runtime.process
    stop = runtime.stop
    monkeypatch.setattr(runtime, "stop", Mock(side_effect=OSError("termination unavailable")))
    manager.disable("test.process")
    state = settled_status()
    assert state["cleanupError"] and not state["terminationConfirmed"]
    assert state["processId"] == process.pid and process.is_alive()
    with pytest.raises(RuntimeError, match="desactivación anterior"):
        manager.enable("test.process")
    monkeypatch.setattr(runtime, "stop", stop)
    manager.disable("test.process")
    state = settled_status()
    assert not process.is_alive()
    assert state["terminationConfirmed"]


@pytest.mark.parametrize("version", [0, 3, True, "2", None])
def test_unknown_runtime_contract_rejected(version):
    with pytest.raises(ValueError, match="runtimeApiVersion"):
        PluginManifest.from_dict(dict(id="test.process", runtimeApiVersion=version))


def test_protocol_preserves_dictionaries_without_type_confusion():
    value = {"$lanctl": "FunctionResult", "fields": {"success": True}, "list": [False]}
    assert _decode(_encode(value)) == value
    with pytest.raises(ValueError):
        _decode(["os.system", {}])


@pytest.mark.parametrize(
    "changes", [dict(version=1), dict(generation="old"), dict(id=True), dict(kind="eval")]
)
def test_protocol_rejects_mismatched_generation_or_schema(changes):
    receive, send = multiprocessing.Pipe()
    try:
        frame = dict(version=2, generation="current", id=1, kind="call", payload={})
        frame.update(changes)
        send.send_bytes(json.dumps(frame).encode())
        with pytest.raises(ValueError):
            _receive(receive, "current")
    finally:
        send.close()
        receive.close()


@pytest.mark.parametrize(
    "payload",
    [b"{}", b"[]", b"\x80\x04N.", b"x" * 65537, b'{"value":NaN}'],
    ids=["object", "array", "pickle", "oversized", "nan"],
)
def test_invalid_frames_are_never_deserialized(payload):
    class Pipe:
        def recv_bytes(self, limit):
            if len(payload) > limit:
                raise OSError("frame exceeds limit")
            return payload

    with pytest.raises((ValueError, OSError)):
        _receive(Pipe(), "generation")


def test_request_budget_is_enforced_in_host(factory):
    manager, create = factory
    with pytest.raises(ValueError, match="presupuesto"):
        create(
            "def activate(api):\n    api.log('one')\n    api.log('two')\n", limits={"maxCalls": 1}
        )
    assert not manager.runtime_status("test.process")["coreAccess"]


def test_direct_network_is_still_denied(factory):
    manager, create = factory
    with pytest.raises(PermissionError, match="política"):
        create("import socket\ndef activate(api):\n    socket.socket()\n")
    assert not manager.runtime_status("test.process")["coreAccess"]


@pytest.mark.parametrize("version", [1, 2])
@pytest.mark.parametrize(
    "event",
    ["os.fork", "os.posix_spawn", "os.exec", "os.kill", "os.startfile", "_winapi.CreateProcess"],
)
def test_process_primitives_cannot_escape_runtime_ownership(factory, version, event):
    _, create = factory
    with pytest.raises(PermissionError, match=r"política|policy"):
        create(f"import sys\ndef activate(api):\n    sys.audit({event!r})\n", api_version=version)


def test_real_posix_fork_is_denied_when_available(factory):
    _, create = factory
    with pytest.raises(PermissionError, match=r"política|policy"):
        create("""
import os, sys
def activate(api):
    if hasattr(os, 'fork'):
        child = os.fork()
        if child == 0:
            os._exit(0)
        os.waitpid(child, 0)
    else:
        sys.audit('os.fork')
""")


def test_callback_timeout_terminates_process(factory):
    manager, create = factory
    plugin = create(
        """
import time
from lanctl.core.plugins.contracts import FunctionResult
def activate(api):
    def hang():
        time.sleep(30)
    api.functions.register('Test.Process.Action.Hang', hang, FunctionResult)
""",
        permissions=["functions.register"],
        limits={"timeoutSeconds": 0.5},
    )
    process = plugin.isolated_runtime.process
    with pytest.raises(TimeoutError):
        manager.functions.call("Test.Process.Action.Hang")
    assert not process.is_alive()
    assert not manager.runtime_status("test.process")["coreAccess"]


def test_v1_shutdown_is_bounded_independently_of_manifest_timeout(factory):
    manager, create = factory
    plugin = create(
        "import time\ndef activate(api): pass\ndef deactivate(): time.sleep(30)\n",
        api_version=1,
        limits={"timeoutSeconds": 60},
    )
    process = plugin.isolated_runtime.process
    started = time.monotonic()
    manager.disable("test.process")
    assert time.monotonic() - started < 4
    assert not process.is_alive()
    assert manager.runtime_status("test.process")["terminationConfirmed"]


def test_failed_v1_termination_retains_process_reference(tmp_path):
    runtime = IsolatedPluginRuntime("test.process", tmp_path / "main.exec")
    runtime.process = process = Mock()
    process.is_alive.return_value = True
    runtime._connection = Mock()
    runtime._reader = Mock()
    runtime._reader.poll.return_value = False
    with pytest.raises(RuntimeError, match="terminación"):
        runtime.stop()
    assert runtime.process is process
    assert process.terminate.called and process.kill.called


@pytest.mark.parametrize("operation", ["install", "uninstall"])
def test_package_files_survive_unconfirmed_process_stop(factory, tmp_path, monkeypatch, operation):
    manager, create = factory
    plugin = create("def activate(api): pass\n")
    runtime = plugin.isolated_runtime
    process = runtime.process
    original = (plugin.path / "main.exec").read_bytes()
    stop = runtime.stop
    monkeypatch.setattr(runtime, "stop", Mock(side_effect=OSError("termination unavailable")))
    package = tmp_path / "test.process.lcp"
    with pytest.raises(RuntimeError, match="desactivación anterior"):
        getattr(manager, operation)(package if operation == "install" else "test.process")
    assert (plugin.path / "main.exec").read_bytes() == original
    assert manager.get("test.process") is plugin
    assert process.is_alive()
    monkeypatch.setattr(runtime, "stop", stop)
    getattr(manager, operation)(package if operation == "install" else "test.process")
    assert not process.is_alive()
    if operation == "uninstall":
        assert not plugin.path.exists()


@pytest.mark.parametrize(
    "entry",
    sorted((Path(__file__).resolve().parents[1] / "packaging/entrypoints").glob("*_entry.py")),
    ids=lambda path: path.stem,
)
def test_frozen_worker_is_dispatched_before_launcher(entry, monkeypatch):
    freeze = Mock(side_effect=SystemExit(37))
    monkeypatch.setattr(multiprocessing, "freeze_support", freeze)
    with pytest.raises(SystemExit) as exit_info:
        runpy.run_path(str(entry), run_name="__main__")
    assert exit_info.value.code == 37
    freeze.assert_called_once()


def test_worker_exits_when_owner_dies_even_without_windows_job(factory, tmp_path):
    manager, create = factory
    create("""
import time, threading
def spin():
    while True:
        time.sleep(.02)
def activate(api):
    threading.Thread(target=spin, daemon=False).start()
def deactivate():
    spin()
""")
    manager.disable("test.process")
    pid_file = tmp_path / "child.pid"
    script = tmp_path / "owner.py"
    script.write_text(
        """
import sys, time
from pathlib import Path
from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins import process_runtime
if __name__ == '__main__':
    PluginManager.audit = lambda *a: None
    process_runtime._windows_memory_job = lambda *a: None
    manager = PluginManager(Path(sys.argv[1]), Path(sys.argv[2]))
    plugin = manager.enable('test.process')
    Path(sys.argv[3]).write_text(str(plugin.isolated_runtime.pid))
    time.sleep(60)
""",
        encoding="utf-8",
    )
    owner = subprocess.Popen(
        [sys.executable, str(script), str(manager.root), str(manager.registry_path), str(pid_file)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    handle = None
    try:
        deadline = time.monotonic() + 10
        while not pid_file.exists() and owner.poll() is None and time.monotonic() < deadline:
            time.sleep(0.05)
        assert pid_file.exists(), "the owner failed to activate its worker"
        pid = int(pid_file.read_text())
        if os.name == "nt":
            from ctypes import wintypes

            from lanctl.core.plugins.isolated_runtime import _windows_kernel

            kernel = _windows_kernel()
            handle = kernel.OpenProcess(0x100000, False, pid)
            assert handle
            kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
            kernel.WaitForSingleObject.restype = wintypes.DWORD
        owner.kill()
        owner.wait(timeout=5)
        if os.name == "nt":
            assert kernel.WaitForSingleObject(handle, 4000) == 0
        else:
            deadline = time.monotonic() + 4
            stat = Path(f"/proc/{pid}/stat")
            while (
                stat.exists() and stat.read_text().split()[2] != "Z" and time.monotonic() < deadline
            ):
                time.sleep(0.05)
            assert not stat.exists() or stat.read_text().split()[2] == "Z"
    finally:
        if owner.poll() is None:
            owner.kill()
        owner.communicate(timeout=5)
        if handle:
            kernel.CloseHandle(handle)
