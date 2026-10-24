"""Revocation must invalidate retained API objects and callback references."""

import json
import subprocess
import sys
import threading
import time

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from lanctl.core.plugins.contracts import FunctionResult
from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.package import build_package


@pytest.fixture
def running(tmp_path, monkeypatch):
    monkeypatch.setattr(PluginManager, "audit", lambda *a: None)
    monkeypatch.setattr("lanctl.core.config.CONFIG_PATH", tmp_path / "config.json")
    from lanctl.core.config import update_config

    update_config(lambda c: c.update({"smbStorage": str(tmp_path / "storage")}))
    key = tmp_path / "test.pem"
    key.write_bytes(
        Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    source = tmp_path / "source"
    source.mkdir()
    permissions = {
        "functions.register",
        "events.listen",
        "plugin.storage",
        "monitor.check.register",
    }
    (source / "plugin.info").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "id": "review.plugin",
                "version": "1.0.0",
                "runtime": "trusted",
                "permissions": sorted(permissions),
            }
        ),
        encoding="utf-8",
    )
    (source / "main.exec").write_text(
        "def activate(api):\n    global saved_api\n    saved_api = api\n", encoding="utf-8"
    )
    package = tmp_path / "review.lcp"
    build_package(source, package, signing_key=key)
    manager = PluginManager(tmp_path / "plugins", tmp_path / "registry.json")
    manager.install(package)
    publisher = manager.publishers.trust_package(package)
    plugin = manager.enable("review.plugin", grant=permissions, trusted=True)
    yield manager, plugin, publisher
    close = getattr(manager, "close", None)
    if close:
        close()


def test_retained_api_is_revoked_after_disable_and_stays_revoked_after_reload(running):
    manager, plugin, _ = running
    old = plugin.module.saved_api
    manager.disable("review.plugin")
    with pytest.raises(PermissionError):
        old.require("functions.register")
    manager.enable("review.plugin", trusted=True)
    plugin.module.saved_api.require("functions.register")
    with pytest.raises(PermissionError):
        old.log("stale reference")


def test_foreign_manager_revocation_blocks_saved_function_and_storage(running):
    manager, plugin, _ = running
    api = plugin.module.saved_api
    calls = []
    api.functions.register(
        "Review.Plugin.Action.Run", lambda: calls.append(1) or FunctionResult(True), FunctionResult
    )
    handler = manager.functions._items["review.plugin.action.run"][1]
    storage = api.storage.open()
    other = PluginManager(manager.root, manager.registry_path)
    other.revoke("review.plugin")
    with pytest.raises(PermissionError):
        handler()
    with pytest.raises(PermissionError):
        storage.put_observation("device", {"value": 1})
    assert calls == []
    assert not storage.path.exists()
    assert manager.runtime_status("review.plugin")["coreAccess"] is False
    assert manager.runtime_status("review.plugin")["restartRequired"] is True


def test_publisher_revocation_rejects_api_without_waiting_for_background_poll(running):
    manager, plugin, publisher = running
    api = plugin.module.saved_api
    manager.publishers.revoke(publisher["fingerprint"])
    with pytest.raises(PermissionError):
        api.settings
    assert not manager.runtime_status("review.plugin")["active"]


def test_deactivation_executes_without_holding_registry_lock(running):
    from lanctl.core.file_transaction import locked_file

    manager, plugin, _ = running
    acquired = threading.Event()

    def deactivate():
        with locked_file(manager.registry_path, timeout=0.2):
            acquired.set()

    plugin.module.deactivate = deactivate
    manager.disable("review.plugin")
    assert acquired.is_set()


def test_hanging_deactivation_does_not_block_revocation_or_allow_reactivation(running):
    manager, plugin, _ = running
    entered, finish = threading.Event(), threading.Event()

    def deactivate():
        entered.set()
        finish.wait(3)

    plugin.module.deactivate = deactivate
    started = time.monotonic()
    try:
        manager.disable("review.plugin")
        assert time.monotonic() - started < 1.5
        assert entered.is_set()
        assert manager.runtime_status("review.plugin")["cleanupPending"]
        with pytest.raises(RuntimeError, match="desactivación anterior"):
            manager.enable("review.plugin", trusted=True)
    finally:
        finish.set()


def test_retained_monitor_check_rejects_execution_and_registry_is_cleaned(running):
    from lanctl.apps.monitor.models import CheckResult

    manager, plugin, _ = running
    called = []
    spec = plugin.module.saved_api.monitor.register_check(
        "review-check", lambda: called.append(1) or CheckResult("review-check", "x", True)
    )
    manager.disable("review.plugin")
    assert not manager.monitor_checks.list()
    with pytest.raises(PermissionError):
        spec.handler()
    assert called == []


def test_background_refresh_reconciles_foreign_manager_without_api_calls(running):
    manager, plugin, _ = running
    manager._authorization.start_watch()
    other = PluginManager(manager.root, manager.registry_path)
    other.disable("review.plugin")
    deadline = time.monotonic() + 3
    while plugin.manifest.plugin_id in manager._active and time.monotonic() < deadline:
        time.sleep(0.05)
    assert plugin.manifest.plugin_id not in manager._active
    assert plugin.module is None


def test_corrupted_authority_fails_closed_without_overwriting_file(running):
    manager, plugin, _ = running
    api = plugin.module.saved_api
    manager.registry_path.write_text("invalid", encoding="utf-8")
    with pytest.raises((ValueError, PermissionError)):
        api.require("plugin.storage")
    assert not manager._active
    assert manager.registry_path.read_text() == "invalid"


def test_revocation_from_separate_process_invalidates_current_api(running):
    manager, plugin, _ = running
    api = plugin.module.saved_api
    subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from pathlib import Path; import sys; "
                "from lanctl.core.plugins.manager import PluginManager; "
                "PluginManager.audit=lambda *a: None; "
                "PluginManager(Path(sys.argv[1]), Path(sys.argv[2])).revoke('review.plugin')"
            ),
            str(manager.root),
            str(manager.registry_path),
        ],
        check=True,
        capture_output=True,
        timeout=20,
    )
    with pytest.raises(PermissionError):
        api.require("functions.register")
    assert not manager.runtime_status("review.plugin")["active"]


def test_revocation_during_function_does_not_report_authorized_success(running):
    manager, plugin, _ = running
    entered, finish = threading.Event(), threading.Event()
    errors = []

    def function():
        entered.set()
        assert finish.wait(3)
        return FunctionResult(True)

    plugin.module.saved_api.functions.register(
        "Review.Plugin.Action.Slow", function, FunctionResult
    )
    handler = manager.functions._items["review.plugin.action.slow"][1]

    def invoke():
        try:
            handler()
        except PermissionError as error:
            errors.append(error)

    thread = threading.Thread(target=invoke)
    thread.start()
    try:
        assert entered.wait(3)
        manager.disable("review.plugin")
    finally:
        finish.set()
        thread.join(3)
    assert not thread.is_alive()
    assert len(errors) == 1


def test_retained_event_callback_is_revoked(running):
    manager, plugin, _ = running
    called = []
    event_id = "LANCTL.Core.Lifecycle.Startup"
    plugin.module.saved_api.events.subscribe(event_id, lambda event: called.append(event))
    handler = manager.events._subscriptions[(event_id.casefold(), 1)][0][2]
    manager.disable("review.plugin")
    with pytest.raises(PermissionError):
        handler(object())
    assert not called


def test_pending_unstarted_cleanup_blocks_new_generation(running, monkeypatch):
    manager, _, _ = running
    drain = manager._authorization.drain
    monkeypatch.setattr(manager._authorization, "drain", lambda: None)
    try:
        manager.disable("review.plugin")
        assert manager.runtime_status("review.plugin")["cleanupPending"]
        with pytest.raises(RuntimeError, match="desactivación anterior"):
            manager.enable("review.plugin", trusted=True)
    finally:
        drain()


def test_registration_cannot_survive_a_concurrent_revocation(running, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    manager, plugin, _ = running
    api = plugin.module.saved_api
    entered, finish = threading.Event(), threading.Event()
    original = manager.functions.register

    def insert(*args, **kwargs):
        entered.set()
        assert finish.wait(3)
        return original(*args, **kwargs)

    monkeypatch.setattr(manager.functions, "register", insert)
    with ThreadPoolExecutor(max_workers=2) as pool:
        registering = pool.submit(
            api.functions.register,
            "Review.Plugin.Action.Race",
            lambda: FunctionResult(True),
            FunctionResult,
        )
        assert entered.wait(3)
        revoking = pool.submit(manager.disable, "review.plugin")
        finish.set()
        registering.result(timeout=3)
        revoking.result(timeout=3)
    assert not manager.functions._items
    with pytest.raises(PermissionError):
        api.functions.register(
            "Review.Plugin.Action.Stale", lambda: FunctionResult(True), FunctionResult
        )


def test_process_rpc_cannot_reintroduce_legacy_native_execution(running, tmp_path):
    manager, legacy, _ = running
    called = []
    legacy.module.saved_api.functions.register(
        "Review.Plugin.Action.Native",
        lambda: called.append(True) or FunctionResult(True),
        FunctionResult,
    )
    source = tmp_path / "process"
    source.mkdir()
    (source / "plugin.info").write_text(
        json.dumps(
            dict(
                schemaVersion=1,
                id="review.process",
                version="1.0.0",
                runtime="isolated",
                runtimeApiVersion=2,
                permissions=["functions.call", "functions.register"],
            )
        ),
        encoding="utf-8",
    )
    (source / "main.exec").write_text(
        """
from lanctl.core.plugins.contracts import FunctionResult
def activate(api):
    def call():
        return api.functions.call('Review.Plugin.Action.Native')
    api.functions.register('Review.Process.Action.Call', call, FunctionResult)
""",
        encoding="utf-8",
    )
    package = tmp_path / "process.lcp"
    build_package(source, package)
    manager.install(package)
    manager.enable("review.process", grant={"functions.call", "functions.register"})
    with pytest.raises(PermissionError, match="heredado"):
        manager.functions.call("Review.Process.Action.Call")
    assert not called
    # Original trusted API remains compatible outside the new process context.
    assert manager.functions.call("Review.Plugin.Action.Native").success


def test_reload_finishes_cleanup_before_new_activation_and_retains_warning(running):
    manager, plugin, _ = running
    previous = plugin.module.saved_api
    closed = []
    plugin.module.deactivate = lambda: closed.append(True)
    manager.reload("review.plugin")
    assert closed == [True]
    assert plugin.module.saved_api is not previous
    assert manager.runtime_status("review.plugin")["restartRequired"]
    manager.discover()
    assert manager.runtime_status("review.plugin")["restartRequired"]


def test_foreign_revocation_cascades_to_dependent_generations(running, tmp_path):
    manager, _, _ = running
    parent = "review.plugin"
    for plugin_id in ("review.child", "review.grandchild"):
        source = tmp_path / plugin_id
        source.mkdir()
        (source / "plugin.info").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "id": plugin_id,
                    "version": "1.0.0",
                    "runtime": "isolated",
                    "depends": [parent],
                }
            ),
            encoding="utf-8",
        )
        package = tmp_path / (plugin_id + ".lcp")
        build_package(source, package)
        manager.install(package)
        manager.enable(plugin_id)
        parent = plugin_id
    other = PluginManager(manager.root, manager.registry_path)
    other.revoke("review.plugin")
    manager.refresh_authorizations()
    for plugin_id in ("review.plugin", "review.child", "review.grandchild"):
        assert not manager.runtime_status(plugin_id)["coreAccess"]
        assert plugin_id not in manager._active


def test_isolated_process_death_retires_runtime(running, tmp_path):
    manager, _, _ = running
    source = tmp_path / "isolated"
    source.mkdir()
    (source / "plugin.info").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "id": "review.isolated",
                "version": "1.0.0",
                "runtime": "isolated",
            }
        ),
        encoding="utf-8",
    )
    (source / "main.exec").write_text("def activate(api):\n    pass\n", encoding="utf-8")
    package = tmp_path / "isolated.lcp"
    build_package(source, package)
    manager.install(package)
    plugin = manager.enable("review.isolated")
    process = plugin.isolated_runtime.process
    process.terminate()
    process.join(3)
    state = manager.runtime_status("review.isolated")
    assert not state["active"] and not state["coreAccess"]
    assert plugin.state.value == "ERROR"
    assert plugin.isolated_runtime is None


def test_concurrent_first_access_creates_one_manager_and_authorization_watcher(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from types import SimpleNamespace
    from unittest.mock import Mock

    from lanctl.core.plugins import manager as module

    created = []
    start = threading.Barrier(8)

    def create():
        time.sleep(0.02)
        instance = SimpleNamespace(_authorization=SimpleNamespace(start_watch=Mock()))
        created.append(instance)
        return instance

    def retrieve():
        start.wait(timeout=3)
        return module.get_plugin_manager()

    monkeypatch.setattr(module, "_MANAGER", None)
    monkeypatch.setattr(module, "PluginManager", create)
    with ThreadPoolExecutor(max_workers=8) as executor:
        found = list(executor.map(lambda _: retrieve(), range(8)))
    assert len(created) == 1
    assert all(item is created[0] for item in found)
    created[0]._authorization.start_watch.assert_called_once()
