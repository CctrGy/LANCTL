import json
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from lanctl.apps.suite.gui import SuiteApi
from lanctl.apps.suite.processes import EmbeddedCli, launcher_command, open_system_cli
from lanctl.core.plugins.settings import PluginSettings


def suite():
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        return SuiteApi()


def test_suite_gui_entrypoint_is_explicit():
    from lanctl.bootstrap.lanctl import main

    with patch("lanctl.apps.suite.gui.run_gui", return_value=0) as run:
        assert main(["--gui"]) == 0
    run.assert_called_once()


def test_project_creation_writes_real_empty_vlf_and_never_overwrites(tmp_path):
    from lanctl.core.projects.vlf import inspect_project, list_project_entries

    api = suite()
    module = "lanctl.apps.ip.interfaces.gui.desktop"
    config = {"projectsDirectory": str(tmp_path), "range": "192.0.2.0/24"}
    with (
        patch(f"{module}.load_config", return_value=config),
        patch(f"{module}.workspace_is_dirty", return_value=False),
        patch(f"{module}.activate_project_workspace") as activate,
        patch.object(api._desktop, "_projects_payload", return_value={}),
        patch.object(api._desktop, "_inventory_payload", return_value={}),
        patch("lanctl.core.plugins.manager.get_plugin_manager") as manager,
    ):
        manager.return_value.project_registry.return_value = {"schemaVersion": 1, "plugins": []}
        result = api.create_project("Oficina", str(tmp_path))
        assert result["ok"], result
        target = tmp_path / "Oficina.vlf"
        original = target.read_bytes()
        assert inspect_project(target)["name"] == "Oficina"
        assert "devices/elements.db" in {entry["path"] for entry in list_project_entries(target)}
        assert not api.create_project("Oficina", str(tmp_path))["ok"]
        assert target.read_bytes() == original
        activate.assert_called_once()


def test_project_failure_never_activates_project(tmp_path):
    api = suite()
    module = "lanctl.apps.ip.interfaces.gui.desktop"
    with (
        patch(f"{module}.load_config", return_value={}),
        patch(f"{module}.workspace_is_dirty", return_value=False),
        patch(f"{module}.create_project", side_effect=OSError("disk full")),
        patch(f"{module}.activate_project_workspace") as activate,
    ):
        assert not api.create_project("Oficina", str(tmp_path))["ok"]
        activate.assert_not_called()


def plugin(tmp_path, plugin_id="demo.settings"):
    return SimpleNamespace(
        path=tmp_path / plugin_id,
        manifest=SimpleNamespace(
            plugin_id=plugin_id,
            raw={
                "settingsSchema": {
                    "schemaVersion": 1,
                    "fields": [
                        {
                            "name": "retries",
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 3,
                        },
                        {"name": "enabled", "type": "boolean", "default": True},
                        {
                            "name": "mode",
                            "type": "select",
                            "choices": ["fast", "normal"],
                            "default": "normal",
                        },
                    ],
                }
            },
        ),
    )


def test_plugin_configuration_roundtrip_isolated_from_other_plugins(tmp_path):
    preferences = PluginSettings(plugin(tmp_path))
    assert preferences.load()["retries"] == 3
    preferences.save({"retries": 7, "enabled": False, "mode": "fast"})
    assert preferences.load() == {"retries": 7, "enabled": False, "mode": "fast"}
    assert PluginSettings(plugin(tmp_path, "other.settings")).load()["retries"] == 3
    assert json.loads(preferences.path.read_text())["schemaVersion"] == 1


def test_wol_configuration_updates_existing_shared_defaults(tmp_path):
    wol = plugin(tmp_path, "lanctl.network.wol")
    wol.manifest.raw = {}
    config = {"wol": {"port": 9, "repeat": 3, "wait": 60, "interval": 0.5}}
    preferences = PluginSettings(wol)
    with (
        patch("lanctl.core.config.load_config", return_value=config),
        patch("lanctl.core.config.update_config", side_effect=lambda update: update(config)),
    ):
        assert preferences.load() == {"port": 9, "repeat": 3, "wait": 60}
        preferences.save({"port": 7, "repeat": 5, "wait": 90})
        assert preferences.load()["port"] == 7
    assert config["wol"]["interval"] == 0.5


def test_isolated_plugin_receives_only_its_settings_snapshot(tmp_path):
    from lanctl.core.plugins.isolated_runtime import IsolatedPluginRuntime

    entry = tmp_path / "main.exec"
    entry.write_text('def activate(api):\n    api.log(str(api.settings["retries"]))\n')
    audit = Mock()
    runtime = IsolatedPluginRuntime("demo.settings", entry, audit=audit, settings={"retries": 7})
    try:
        runtime.start()
        assert any("7" in call.args for call in audit.call_args_list)
    finally:
        runtime.stop()


@pytest.mark.parametrize(
    "values",
    [
        {"retries": True, "enabled": False, "mode": "fast"},
        {"retries": 100, "enabled": False, "mode": "fast"},
        {"retries": 3, "enabled": "false", "mode": "fast"},
        {"retries": 3, "enabled": True, "mode": "invalid"},
        {"retries": 3},
    ],
)
def test_plugin_configuration_rejects_invalid_values(tmp_path, values):
    preferences = PluginSettings(plugin(tmp_path))
    with pytest.raises(ValueError):
        preferences.save(values)
    assert not preferences.path.exists()


def test_corrupt_plugin_preferences_are_not_treated_as_defaults(tmp_path):
    preferences = PluginSettings(plugin(tmp_path))
    preferences.path.parent.mkdir(parents=True)
    preferences.path.write_text('{"schemaVersion":99,"values":{}}')
    with pytest.raises(ValueError):
        preferences.load()
    with pytest.raises(ValueError):
        preferences.save({"retries": 7, "enabled": False, "mode": "fast"})


def test_external_cli_windows_uses_default_console_and_argv():
    with (
        patch(
            "lanctl.apps.suite.processes.sys",
            SimpleNamespace(platform="win32", executable=sys.executable),
        ),
        patch("lanctl.apps.suite.processes.subprocess.CREATE_NEW_CONSOLE", 0x10, create=True),
        patch("lanctl.apps.suite.processes.subprocess.Popen") as popen,
    ):
        open_system_cli()
    args, kwargs = popen.call_args
    assert args[0][-1] == "--cli"
    assert "shell" not in kwargs
    assert kwargs["creationflags"] == 0x10


def test_external_cli_linux_uses_default_terminal():
    with (
        patch(
            "lanctl.apps.suite.processes.sys",
            SimpleNamespace(platform="linux", executable=sys.executable),
        ),
        patch(
            "lanctl.apps.suite.processes.shutil.which", return_value="/usr/bin/x-terminal-emulator"
        ),
        patch("lanctl.apps.suite.processes.subprocess.Popen") as popen,
    ):
        open_system_cli()
    assert popen.call_args.args[0][:2] == ["/usr/bin/x-terminal-emulator", "-e"]
    assert popen.call_args.args[0][-1] == "--cli"


def test_gui_does_not_launch_cli_as_a_fallback():
    api = suite()
    with patch("lanctl.apps.suite.gui.subprocess.Popen") as popen:
        assert not api.launch_gui("unknown")["ok"]
    popen.assert_not_called()


def test_embedded_cli_runs_real_version_command_and_closes(tmp_path, monkeypatch):
    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LANCTL_SECRET_DIR", str(tmp_path / "secrets"))
    console = EmbeddedCli()
    output = ""
    try:
        console.start()
        console.send("version")
        console.send("exit")
        for _ in range(200):
            result = console.output()
            output += result["text"]
            if not result["running"] and "LANCTL" in output:
                break
            time.sleep(0.05)
        from lanctl import __version__

        assert __version__ in output
        assert "LANCTL" in output
    finally:
        console.close()


def test_no_arbitrary_launcher_or_multiline_cli_input():
    with pytest.raises(ValueError):
        launcher_command("powershell", "-Command", "anything")
    with pytest.raises(ValueError):
        EmbeddedCli().send("version\nexit")


def test_gui_settings_catalog_and_edit_use_shared_validation(tmp_path, monkeypatch):
    from lanctl.core import config
    from lanctl.core.settings_catalog import catalog

    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    api = suite()
    payload = api.settings_catalog()
    assert payload["ok"]
    paths = {entry["path"] for entry in payload["entries"]}
    assert {"gui.theme", "startup.closeGuiOnLaunch", "ip.workers", "projects.saveMode"} <= paths
    assert paths - {"access.remote"} < {e["path"] for e in catalog(config.load_config())}
    assert not paths & {
        "tui.panelLayout",
        "cli.commandChaining",
        "ip.listColumns",
        "access.users",
        "schemaVersion",
    }
    assert api.save_catalog_setting("program", "ip.workers", 12)["ok"]
    assert config.load_config()["workers"] == 12
    before = config.CONFIG_PATH.read_bytes()
    for path, value in [
        ("cli.commandChaining", False),
        ("tui.panelLayout", "cli.top"),
        ("access.users", "other.json"),
    ]:
        assert not api.save_catalog_setting("program", path, value)["ok"]
    assert not api.save_catalog_setting("program", "ip.workers", 0)["ok"]
    assert config.CONFIG_PATH.read_bytes() == before
    assert not api.save_catalog_setting("unknown", "ip.workers", 10)["ok"]


def test_project_defaults_do_not_require_a_folder_picker(tmp_path, monkeypatch):
    from lanctl.core import config

    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    config.save_config({**config.load_config(), "projectsDirectory": str(tmp_path / "Projects")})
    api = suite()
    payload = api.project_defaults()
    assert payload["ok"]
    assert payload["directory"] == str(tmp_path / "Projects")
    assert payload["lan"] == "LAN principal"


@pytest.mark.parametrize(
    "package_id,signature,accepted",
    [
        ("test.plugin", "VALID_ED25519:example", True),
        ("test.plugin", "UNSIGNED", False),
        ("other.plugin", "VALID_ED25519:example", False),
    ],
)
def test_signed_plugin_replacement_checks_identity_and_signature(package_id, signature, accepted):
    api = suite()
    api._desktop._window = Mock()
    api._desktop._window.create_file_dialog.return_value = ["signed.lcp"]
    verified = {"manifest": SimpleNamespace(plugin_id=package_id), "signature": signature}
    with (
        patch("lanctl.apps.suite.gui.get_plugin_manager") as manager,
        patch("lanctl.core.plugins.package.verify_package", return_value=verified),
        patch.object(api, "_plugin_payload", return_value={"plugins": []}),
    ):
        result = api.install_signed_plugin("test.plugin")
        assert result["ok"] is accepted
        assert manager.return_value.install.called is accepted
        manager.return_value.publishers.trust_package.assert_not_called()
