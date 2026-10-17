"""Backend regressions for the plugin audit of 2026-10-16."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
from unittest.mock import Mock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.models import PluginState
from lanctl.core.plugins.package import build_package
from lanctl.core.plugins.publishers import TrustedPublisherStore


@pytest.fixture
def factory(tmp_path, monkeypatch):
    monkeypatch.setattr(PluginManager, "audit", Mock())
    key = tmp_path / "publisher.pem"
    key.write_bytes(
        Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )

    def create(plugin_id="test.plugin", *, signed=True, runtime="trusted", **fields):
        source = tmp_path / "sources" / plugin_id
        source.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schemaVersion": 1,
            "id": plugin_id,
            "name": plugin_id,
            "version": "1.0.0",
            "runtime": runtime,
            "permissions": ["theme.register"],
            **fields,
        }
        (source / "plugin.info").write_text(json.dumps(manifest), encoding="utf-8")
        (source / "main.exec").write_text(
            "def activate(api):\n    api.log('EXECUTED')\n", encoding="utf-8"
        )
        package = tmp_path / f"{plugin_id}.lcp"
        build_package(source, package, overwrite=True, signing_key=key if signed else None)
        return package

    manager = PluginManager(tmp_path / "plugins", tmp_path / "registry.json")
    return manager, create


def authorize(manager, package):
    plugin = manager.install(package)
    manager.publishers.trust_package(package)
    return manager.enable(plugin.manifest.plugin_id, grant={"theme.register"}, trusted=True)


def edit_registry(manager, plugin_id, **changes):
    document = json.loads(manager.registry_path.read_text(encoding="utf-8"))
    document["plugins"][plugin_id].update(changes)
    manager.registry_path.write_text(json.dumps(document), encoding="utf-8")


@pytest.mark.parametrize("operation", ["verify", "enable", "reload"])
def test_changed_installed_code_is_never_verified_or_executed(factory, operation):
    manager, create = factory
    plugin = authorize(manager, create())
    manager.disable("test.plugin")
    (plugin.path / "main.exec").write_text(
        "def activate(api):\n    api.log('TAMPERED')\n", encoding="utf-8"
    )
    manager.audit.reset_mock()
    with pytest.raises(ValueError, match=r"integridad|checksum"):
        getattr(manager, operation)("test.plugin")
    assert not any(c.args[1] == "TAMPERED" for c in manager.audit.call_args_list)


def test_removed_signature_is_not_recovered_from_cached_registry(factory):
    manager, create = factory
    plugin = authorize(manager, create())
    manager.disable("test.plugin")
    (plugin.path / "meta/signature").unlink()
    fresh = PluginManager(manager.root, manager.registry_path)
    assert fresh.get("test.plugin").state == PluginState.QUARANTINED
    with pytest.raises((ValueError, PermissionError)):
        fresh.enable("test.plugin")


def test_discovery_recovers_signature_of_preinstalled_signed_package(factory):
    from lanctl.core.plugins.package import install_package

    manager, create = factory
    install_package(create(), manager.root)
    fresh = PluginManager(manager.root, manager.registry_path)
    assert fresh.get("test.plugin").signature.startswith("VALID_ED25519:")
    assert not fresh.publishers.is_trusted(fresh.get("test.plugin").signature)


@pytest.mark.parametrize(
    "changes",
    [
        {"granted": []},
        {"granted": ["theme.register", "credentials.read.scoped"]},
    ],
)
def test_startup_revalidates_grants_before_loading_code(factory, changes):
    manager, create = factory
    authorize(manager, create())
    edit_registry(manager, "test.plugin", **changes)
    fresh = PluginManager(manager.root, manager.registry_path)
    fresh.activate_enabled()
    assert fresh.get("test.plugin").state != PluginState.ENABLED
    assert fresh.get("test.plugin").module is None
    assert fresh.get("test.plugin").error


def test_startup_rechecks_lanctl_compatibility(factory, monkeypatch):
    manager, create = factory
    authorize(manager, create(lanctl={"maximumVersion": "0.x"}))
    fresh = PluginManager(manager.root, manager.registry_path)
    monkeypatch.setattr("lanctl.core.plugins.manager.__version__", "1.0.0")
    fresh.activate_enabled()
    assert fresh.get("test.plugin").state == PluginState.INCOMPATIBLE
    assert fresh.get("test.plugin").module is None


def test_repeated_enable_does_not_run_activation_twice(factory):
    manager, create = factory
    plugin = authorize(manager, create())
    module = plugin.module
    manager.audit.reset_mock()
    manager.enable("test.plugin")
    assert plugin.module is module
    assert not any(c.args[1] == "EXECUTED" for c in manager.audit.call_args_list)


def test_failed_grant_change_cleans_up_running_plugin(factory):
    manager, create = factory
    plugin = authorize(manager, create())
    plugin.module.deactivate = Mock()
    deactivate = plugin.module.deactivate
    with pytest.raises(PermissionError):
        manager.enable("test.plugin", grant=set())
    deactivate.assert_called_once()
    assert plugin.module is None
    assert plugin.state == PluginState.BLOCKED


def test_unsigned_trusted_block_has_persistent_reason(factory):
    manager, create = factory
    manager.install(create(signed=False))
    with pytest.raises(PermissionError, match=r"firma|firmado"):
        manager.enable("test.plugin", grant={"theme.register"}, trusted=True)
    plugin = manager.get("test.plugin")
    assert plugin.state == PluginState.BLOCKED and plugin.error
    fresh = PluginManager(manager.root, manager.registry_path)
    assert fresh.get("test.plugin").error == plugin.error


@pytest.mark.parametrize(
    "document", [[], {"schemaVersion": 999, "plugins": {}}, {"schemaVersion": 1, "plugins": []}]
)
def test_corrupt_registry_is_not_treated_as_empty(factory, document):
    manager, _ = factory
    manager.registry_path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="registro"):
        PluginManager(manager.root, manager.registry_path)
    assert json.loads(manager.registry_path.read_text(encoding="utf-8")) == document


@pytest.mark.parametrize(
    "document",
    [[], {"schemaVersion": 999, "publishers": {}}, {"schemaVersion": 1, "publishers": {"bad": {}}}],
)
def test_malformed_publisher_store_reports_validation_error(tmp_path, document):
    path = tmp_path / "publishers.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(ValueError, match="almacén"):
        TrustedPublisherStore(path).list()


def test_dependency_order_at_startup_is_independent_of_display_name(factory):
    manager, create = factory
    authorize(manager, create("test.dependency", name="ZZZ"))
    authorize(manager, create("test.consumer", name="AAA", depends=["test.dependency"]))
    fresh = PluginManager(manager.root, manager.registry_path)
    order = []
    original = fresh._activate

    def record(plugin):
        order.append(plugin.manifest.plugin_id)
        original(plugin)

    fresh._activate = record
    fresh.activate_enabled()
    assert order.index("test.dependency") < order.index("test.consumer")


def test_dependency_version_is_checked(factory):
    manager, create = factory
    authorize(manager, create("test.dependency"))
    package = create("test.consumer", depends=[{"id": "test.dependency", "version": ">=2.0.0"}])
    manager.install(package)
    with pytest.raises(ValueError, match="dependencia"):
        manager.enable("test.consumer", grant={"theme.register"}, trusted=True)


def test_reinstall_releases_previous_runtime(factory):
    manager, create = factory
    plugin = authorize(manager, create())
    plugin.module.deactivate = Mock()
    deactivate = plugin.module.deactivate
    replacement = manager.install(create(version="1.1.0"))
    deactivate.assert_called_once()
    assert replacement.state == PluginState.DISABLED
    assert not replacement.granted and not replacement.trusted


def test_quarantine_remains_visible_after_another_restart(factory):
    manager, create = factory
    plugin = authorize(manager, create())
    manager.disable("test.plugin")
    (plugin.path / "meta/signature").write_text("{}", encoding="utf-8")
    first = PluginManager(manager.root, manager.registry_path)
    assert first.get("test.plugin").state == PluginState.QUARANTINED
    second = PluginManager(manager.root, manager.registry_path)
    assert second.get("test.plugin").state == PluginState.QUARANTINED
    with pytest.raises(ValueError, match="integridad"):
        second.enable("test.plugin", grant={"theme.register"}, trusted=True)


def test_quarantine_history_does_not_resurrect_uninstalled_plugin(factory):
    manager, create = factory
    plugin = authorize(manager, create())
    manager.disable("test.plugin")
    (plugin.path / "meta/signature").write_text("{}", encoding="utf-8")
    fresh = PluginManager(manager.root, manager.registry_path)
    assert fresh.get("test.plugin").state == PluginState.QUARANTINED
    fresh.install(create(version="1.1.0"))
    fresh.uninstall("test.plugin")
    restarted = PluginManager(manager.root, manager.registry_path)
    assert "test.plugin" not in {p.manifest.plugin_id for p in restarted.list()}


def test_startup_does_not_load_consumer_when_dependency_fails(factory):
    manager, create = factory
    authorize(manager, create("test.dependency"))
    authorize(manager, create("test.consumer", depends=["test.dependency"]))
    edit_registry(manager, "test.dependency", granted=[])
    fresh = PluginManager(manager.root, manager.registry_path)
    fresh.activate_enabled()
    assert fresh.get("test.dependency").state == PluginState.ERROR
    assert fresh.get("test.consumer").state == PluginState.ERROR
    assert fresh.get("test.consumer").module is None


def test_dependency_cycles_are_reported_without_loading_code(factory):
    manager, create = factory
    for plugin_id, dependency in (("test.first", "test.second"), ("test.second", "test.first")):
        package = create(plugin_id, depends=[dependency])
        manager.install(package)
        manager.publishers.trust_package(package)
    for plugin_id in ("test.first", "test.second"):
        edit_registry(manager, plugin_id, state="ENABLED", granted=["theme.register"], trusted=True)
    fresh = PluginManager(manager.root, manager.registry_path)
    fresh.activate_enabled()
    for plugin_id in ("test.first", "test.second"):
        assert fresh.get(plugin_id).state == PluginState.ERROR
        assert fresh.get(plugin_id).module is None


def test_disabling_dependency_unloads_its_consumers(factory):
    manager, create = factory
    authorize(manager, create("test.dependency"))
    authorize(manager, create("test.consumer", depends=["test.dependency"]))
    manager.disable("test.dependency")
    assert manager.get("test.consumer").state == PluginState.DISABLED
    assert manager.get("test.consumer").module is None


def test_discovery_releases_previous_runtime_before_reactivation(factory):
    manager, create = factory
    plugin = authorize(manager, create())
    plugin.module.deactivate = Mock()
    deactivate = plugin.module.deactivate
    manager.discover()
    deactivate.assert_called_once()
    manager.activate_enabled()
    assert manager.get("test.plugin").module is not None


def test_other_plugin_update_does_not_restore_revoked_permissions(factory):
    manager, create = factory
    authorize(manager, create("test.first"))
    authorize(manager, create("test.second"))
    another = PluginManager(manager.root, manager.registry_path)
    another.revoke("test.first")
    manager.disable("test.second")
    saved = json.loads(manager.registry_path.read_text(encoding="utf-8"))["plugins"]
    assert saved["test.first"]["granted"] == []
    assert saved["test.first"]["state"] == "DISABLED"
    assert saved["test.second"]["state"] == "DISABLED"
    with pytest.raises(ValueError, match="otro proceso"):
        manager.enable("test.first")
    assert manager.get("test.first").module is None
    assert manager.get("test.first").state == PluginState.BLOCKED


def test_two_managers_install_different_plugins_without_losing_entries(factory):
    first, create = factory
    second = PluginManager(first.root, first.registry_path)
    first.install(create("test.first"))
    second.install(create("test.second"))
    saved = json.loads(first.registry_path.read_text(encoding="utf-8"))["plugins"]
    assert {"test.first", "test.second"} <= saved.keys()


def test_stale_install_cannot_replace_a_package_installed_by_another_manager(factory):
    first, create = factory
    second = PluginManager(first.root, first.registry_path)
    installed = first.install(create())
    original_info = (installed.path / "plugin.info").read_bytes()
    with pytest.raises(ValueError, match="otro proceso"):
        second.install(create(version="2.0.0"))
    assert (installed.path / "plugin.info").read_bytes() == original_info


def test_startup_refreshes_revocation_made_after_discovery(factory):
    manager, create = factory
    authorize(manager, create())
    fresh = PluginManager(manager.root, manager.registry_path)
    manager.revoke("test.plugin")
    fresh.activate_enabled()
    assert fresh.get("test.plugin").state == PluginState.DISABLED
    assert fresh.get("test.plugin").module is None


def test_failure_to_persist_activation_unloads_the_runtime(factory, monkeypatch):
    manager, create = factory
    package = create()
    manager.install(package)
    manager.publishers.trust_package(package)
    original_registry = manager.registry_path.read_bytes()

    def fail_write(*args, **kwargs):
        raise OSError("simulated disk failure")

    monkeypatch.setattr("lanctl.core.plugins.manager.atomic_write_json", fail_write)
    with pytest.raises(OSError, match="simulated disk failure"):
        manager.enable("test.plugin", grant={"theme.register"}, trusted=True)
    assert manager.get("test.plugin").module is None
    assert manager.get("test.plugin").state == PluginState.BLOCKED
    assert manager.registry_path.read_bytes() == original_registry


def test_failure_to_persist_startup_unloads_all_runtimes(factory, monkeypatch):
    manager, create = factory
    authorize(manager, create())
    fresh = PluginManager(manager.root, manager.registry_path)

    def fail_write(*args, **kwargs):
        raise OSError("simulated startup disk failure")

    monkeypatch.setattr("lanctl.core.plugins.manager.atomic_write_json", fail_write)
    with pytest.raises(OSError, match="simulated startup disk failure"):
        fresh.activate_enabled()
    assert not fresh.initialized
    assert not fresh._active
    assert all(p.module is None and p.isolated_runtime is None for p in fresh.list())


def test_trusting_another_editor_cannot_restore_concurrently_revoked_editor(factory, monkeypatch):
    manager, create = factory
    original_package = create("test.original")
    original = manager.publishers.trust_package(original_package)
    # A second publisher uses a different key.
    key = original_package.parent / "publisher.pem"
    key.write_bytes(
        Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    new_package = create("test.new")
    first = TrustedPublisherStore(manager.publishers.path)
    second = TrustedPublisherStore(manager.publishers.path)
    read_started, continue_write = Event(), Event()
    original_read = first._read

    def slow_read():
        value = original_read()
        read_started.set()
        assert continue_write.wait(5)
        return value

    monkeypatch.setattr(first, "_read", slow_read)
    with ThreadPoolExecutor(max_workers=2) as pool:
        trust = pool.submit(first.trust_package, new_package)
        assert read_started.wait(5)
        revoke = pool.submit(second.revoke, original["fingerprint"])
        continue_write.set()
        added = trust.result(timeout=5)
        assert revoke.result(timeout=5)
    assert [p["fingerprint"] for p in manager.publishers.list()] == [added["fingerprint"]]


@pytest.mark.parametrize("plugin_id", ["lanctl.network.wol", "lanctl.discovery.mdns-ssdp"])
def test_bundled_trusted_plugins_cannot_bypass_signature_using_all_permissions(factory, plugin_id):
    manager, _ = factory
    # Build unsigned fixtures so publishing signed official packages later does
    # not make this negative test depend on the current distribution problem.
    package = manager.registry_path.parent / "unsigned-fixture.lcp"
    build_package(Path(__file__).resolve().parents[1] / "plugins-src" / plugin_id, package)
    plugin = manager.install(package)
    assert plugin.signature == "UNSIGNED"
    with pytest.raises(PermissionError, match="firmado"):
        manager.enable(plugin_id, grant=set(plugin.manifest.permissions), trusted=True)
    assert plugin.module is None
    assert plugin.state == PluginState.BLOCKED


@pytest.mark.parametrize(
    "requirement, expected",
    [
        ("*", True),
        ("1.x", True),
        ("1.0.*", True),
        (">=1.0.0,<2.0.0", True),
        ("==1.0.0", True),
        ("!=1.x", False),
        (">=2.0.0", False),
        ("2.0.0", False),
    ],
)
def test_dependency_constraints(requirement, expected):
    from lanctl.core.plugins.manager import _matches_dependency

    assert _matches_dependency("1.0.0", requirement) is expected
