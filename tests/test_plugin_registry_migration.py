"""P44: migrate the historical empty registry without recovering authorization."""

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from lanctl.core.file_transaction import atomic_write_json, locked_file
from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.models import PluginState
from lanctl.core.plugins.package import build_package


@pytest.fixture
def manager(tmp_path, monkeypatch):
    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LANCTL_SECRET_DIR", str(tmp_path / "secrets"))
    return PluginManager(tmp_path / "installed", tmp_path / "registry.json")


@pytest.mark.parametrize("original", [b"{}", b" \n{ \n }\r\n"])
def test_only_historical_empty_object_migrates_once(manager, original, monkeypatch):
    manager.registry_path.write_bytes(original)
    assert manager._read_registry() == {}
    assert json.loads(manager.registry_path.read_bytes()) == {"schemaVersion": 1, "plugins": {}}
    migrated = manager.registry_path.read_bytes()

    def unexpected_write(*args, **kwargs):
        pytest.fail("An already migrated registry must not be rewritten by reading it")

    monkeypatch.setattr("lanctl.core.plugins.manager.atomic_write_json", unexpected_write)
    assert manager._read_registry() == {}
    assert manager.registry_path.read_bytes() == migrated


def test_versioned_registry_preserves_permissions_and_unknown_fields_byte_for_byte(manager):
    document = {
        "schemaVersion": 1,
        "futureMetadata": {"keep": True},
        "plugins": {
            "test.existing": {
                "state": "DISABLED",
                "trusted": False,
                "granted": ["theme.register"],
                "futureField": [1, 2],
            }
        },
    }
    original = json.dumps(document, indent=4).encode()
    manager.registry_path.write_bytes(original)
    assert manager._read_registry() == document["plugins"]
    assert manager.registry_path.read_bytes() == original


@pytest.mark.parametrize(
    "original",
    [
        b"",
        b"{",
        b"[]",
        b"null",
        b"false",
        b'{"plugins": {}}',
        b'{"unexpected": "data"}',
        b'{"schemaVersion": 999, "plugins": {}}',
        b'{"schemaVersion": 1, "plugins": []}',
        b'{"schemaVersion": 1, "plugins": {"test": {"trusted": "yes"}}}',
    ],
)
def test_malformed_or_unknown_registry_is_rejected_without_rewriting(manager, original):
    manager.registry_path.write_bytes(original)
    with pytest.raises(ValueError, match="registro de plugins") as caught:
        manager._read_registry()
    assert caught.value.__cause__ is not None
    assert manager.registry_path.read_bytes() == original


def test_failed_migration_preserves_original_and_error_origin(manager, monkeypatch):
    original = b"{}\n"
    manager.registry_path.write_bytes(original)
    failure = OSError("P44 simulated disk failure")
    reported = []

    def fail_write(*args, **kwargs):
        raise failure

    def report(error, **details):
        reported.append((error, details))

    monkeypatch.setattr("lanctl.core.plugins.manager.atomic_write_json", fail_write)
    monkeypatch.setattr("lanctl.core.errors.errors.from_exception", report)
    with pytest.raises(ValueError, match="registro de plugins") as caught:
        manager._read_registry()
    assert caught.value.__cause__ is failure
    assert reported[0][0] is failure
    assert reported[0][1]["origin"] == "LANCTL.Plugin.Registry.Load"
    assert manager.registry_path.read_bytes() == original


def test_migration_waits_for_writer_and_preserves_new_authorization(manager):
    manager.registry_path.write_text("{}", encoding="utf-8")
    started, finished = Event(), Event()
    document = {
        "schemaVersion": 1,
        "plugins": {"test.concurrent": {"state": "DISABLED", "trusted": False, "granted": []}},
    }

    def read():
        started.set()
        try:
            return manager._read_registry()
        finally:
            finished.set()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with locked_file(manager.registry_path):
            future = pool.submit(read)
            assert started.wait(5)
            assert not finished.wait(0.15), "Reader bypassed the registry writer's lock"
            atomic_write_json(manager.registry_path, document)
        assert future.result(timeout=5) == document["plugins"]
    assert json.loads(manager.registry_path.read_bytes()) == document


def test_migrating_empty_registry_does_not_restore_trust_or_grants(manager, tmp_path):
    source = tmp_path / "plugin-source"
    source.mkdir()
    manifest = {
        "schemaVersion": 1,
        "id": "test.previous-trust",
        "name": "Previously installed plugin",
        "version": "1.0.0",
        "runtime": "trusted",
        "entryPoint": "main.exec",
        "defaultEnabled": True,
        "permissions": ["theme.register"],
    }
    (source / "plugin.info").write_text(json.dumps(manifest), encoding="utf-8")
    (source / "main.exec").write_text(
        "raise RuntimeError('This plugin must not execute during migration')\n", encoding="utf-8"
    )
    package = tmp_path / "plugin.lcp"
    build_package(source, package)
    manager.install(package)
    manager.registry_path.write_text("{}", encoding="utf-8")
    restored = PluginManager(manager.root, manager.registry_path).get(manifest["id"])
    assert restored.state == PluginState.DISABLED
    assert restored.granted == set()
    assert restored.trusted is False
    assert restored.module is None


@pytest.mark.parametrize("legacy", [False, True], ids=["fresh", "legacy-empty"])
def test_lanip_gui_bootstrap_uses_real_migration_and_registry(tmp_path, legacy):
    # Fresh interpreter: path defaults and the plugin singleton belong to this data directory.
    script = """
import json
import os
from pathlib import Path
from unittest.mock import patch
root = Path(os.environ['LANCTL_DATA_DIR'])
from lanctl.core.file_transaction import atomic_write_text
atomic_write_text(root / 'config/migration-v2.complete', 'LANCTL-DATA-V2\\n')
from lanctl.core.data_migration import ensure_data_layout
ensure_data_layout()
registry = root / 'plugins/registry.json'
if os.environ['P44_LEGACY'] == '1':
    registry.write_text('{}', encoding='utf-8')
from lanctl.core.config import load_config, save_config
config = load_config()
config.update(pluginSafeMode=True, projectsDirectory=str(root / 'projects-test'))
save_config(config)
from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
from lanctl.bootstrap.lanip import main
def gui():
    result = DesktopApi().bootstrap()
    assert result['ok'], result
    return 0
with patch('lanctl.apps.ip.interfaces.gui.desktop.run_gui', side_effect=gui) as launch:
    assert main(['--gui']) == 0
    launch.assert_called_once()
assert json.loads(registry.read_text(encoding='utf-8'))['schemaVersion'] == 1
print('P44_BOOTSTRAP_OK')
"""
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
    result = subprocess.run(
        [sys.executable, "-c", script],
        env={
            **os.environ,
            "LANCTL_DATA_DIR": str(tmp_path / "data"),
            "LANCTL_SECRET_DIR": str(tmp_path / "secrets"),
            "P44_LEGACY": str(int(legacy)),
        },
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=40,
        **options,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "P44_BOOTSTRAP_OK" in result.stdout
