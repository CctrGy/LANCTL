import json
from threading import RLock
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from lanctl.apps.suite.gui import SuiteApi
from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.models import PluginState
from lanctl.core.plugins.package import build_package


@pytest.fixture
def installed(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    (source / "plugin.info").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "id": "demo.trust-test",
                "name": "Trust test",
                "version": "1.0.0",
                "entryPoint": "main.exec",
                "runtime": "trusted",
                "permissions": ["theme.register"],
                "capabilities": ["theme"],
                "lanctl": {"minimumVersion": "0.3.0", "maximumVersion": "0.x"},
            }
        ),
        encoding="utf-8",
    )
    (source / "main.exec").write_text("def activate(api):\n    api.log('ACTIVATE')\n")
    key = tmp_path / "key.pem"
    key.write_bytes(
        Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    package = tmp_path / "signed.lcp"
    build_package(source, package, signing_key=key)
    manager = PluginManager(tmp_path / "plugins", tmp_path / "registry.json")
    manager.install(package)
    api = SuiteApi.__new__(SuiteApi)
    api._lock = RLock()
    api._desktop = SimpleNamespace(_window=Mock())
    monkeypatch.setattr("lanctl.apps.suite.gui.get_plugin_manager", lambda: manager)
    return api, manager, package


def test_signed_plugin_gui_requires_publisher_then_permissions_and_preserves_revoke(installed):
    api, manager, package = installed
    plugin_id = "demo.trust-test"
    assert not api.set_plugin_enabled(plugin_id, True, ["theme.register"], True)["ok"]
    api._desktop._window.create_file_dialog.return_value = [str(package)]
    result = api.trust_plugin_publisher(plugin_id)
    assert result["ok"], result
    assert next(p for p in result["plugins"] if p["id"] == plugin_id)["publisherTrusted"]
    assert api.set_plugin_enabled(plugin_id, True, ["theme.register"], True)["ok"]
    assert manager.get(plugin_id).state == PluginState.ENABLED
    assert api.set_plugin_enabled(plugin_id, False)["ok"]
    manager.publishers.revoke(manager.get(plugin_id).signature.split(":", 1)[1])
    assert not api.set_plugin_enabled(plugin_id, True, ["theme.register"], True)["ok"]


def test_publisher_dialog_cancel_or_wrong_package_never_grants_trust(installed):
    api, manager, package = installed
    api._desktop._window.create_file_dialog.return_value = None
    assert api.trust_plugin_publisher("demo.trust-test")["cancelled"]
    api._desktop._window.create_file_dialog.return_value = [str(package)]
    assert not api.trust_plugin_publisher("lanctl.network.wol")["ok"]
    assert not manager.publishers.is_trusted(manager.get("demo.trust-test").signature)
    assert not api.set_plugin_enabled(
        "lanctl.network.wol",
        True,
        ["network.udp", "functions.register", "ui-action.register"],
        True,
    )["ok"]


def test_configuration_visibility_uses_schema_not_saved_file_and_refreshes(installed):
    api, manager, _ = installed
    plugin = manager.get("demo.trust-test")
    # Test the in-memory fallback for a caller without a package directory.
    plugin.path = plugin.path.parent / "not-materialized"
    assert api._configuration_status(plugin) == {"hasSettings": False, "settingsError": ""}
    plugin.manifest.raw["settingsSchema"] = {
        "schemaVersion": 1,
        "fields": [{"name": "test", "type": "text", "default": "value"}],
    }
    assert api._configuration_status(plugin)["hasSettings"]
    assert api.plugin_settings(plugin.manifest.plugin_id)["values"] == {"test": "value"}
    assert not (plugin.path.parent / ".settings").exists()
    plugin.manifest.raw["settingsSchema"]["fields"] = []
    assert not api._configuration_status(plugin)["hasSettings"]
    plugin.manifest.raw["settingsSchema"] = {"schemaVersion": 100}
    status = api._configuration_status(plugin)
    assert not status["hasSettings"] and status["settingsError"]


def test_existing_gui_reads_configuration_schema_after_external_package_update(installed):
    api, manager, _ = installed
    plugin = manager.get("demo.trust-test")
    assert not api._configuration_status(plugin)["hasSettings"]
    path = plugin.path / "plugin.info"
    current = json.loads(path.read_text(encoding="utf-8"))
    current["settingsSchema"] = {
        "schemaVersion": 1,
        "fields": [{"name": "label", "type": "text", "default": "Updated"}],
    }
    path.write_text(json.dumps(current), encoding="utf-8")
    assert "settingsSchema" not in plugin.manifest.raw
    assert api._configuration_status(plugin)["hasSettings"]
    assert api.plugin_settings(plugin.manifest.plugin_id)["values"] == {"label": "Updated"}
    current["settingsSchema"]["fields"] = []
    path.write_text(json.dumps(current), encoding="utf-8")
    assert not api._configuration_status(plugin)["hasSettings"]
    path.write_text("[]", encoding="utf-8")
    status = api._configuration_status(plugin)
    assert not status["hasSettings"] and status["settingsError"]


def test_same_content_signed_by_another_publisher_does_not_grant_trust(installed, monkeypatch):
    from lanctl.core.plugins.package import verify_package

    api, manager, package = installed
    result = verify_package(package)
    result["signature"] = "VALID_ED25519:different-publisher"
    monkeypatch.setattr("lanctl.core.plugins.package.verify_package", lambda _: result)
    grant = Mock()
    monkeypatch.setattr(manager.publishers, "trust_package", grant)
    api._desktop._window.create_file_dialog.return_value = [str(package)]
    assert not api.trust_plugin_publisher("demo.trust-test")["ok"]
    grant.assert_not_called()
