"""Regressions for REF-P69: authorization and whole-batch validation."""

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.apps.ip.interfaces.cli.commands.settings import register_settings_command, run_settings
from lanctl.apps.suite.settings import save_form_values, save_program_changes, settings_entries
from lanctl.core import config
from lanctl.core.settings_catalog import set_program_value
from lanctl.core.settings_policy import SettingsContext


def cli_args(*arguments):
    parser = argparse.ArgumentParser()
    register_settings_command(parser.add_subparsers())
    return parser.parse_args(["settings", *arguments])


@pytest.mark.parametrize("interface", ["cli", "gui", "tui", "direct", "remote"])
@pytest.mark.parametrize(
    "path",
    [
        "plugins.registry",
        "storage.credentials",
        "projects.workspace.databases.physical",
        "access.users",
    ],
)
def test_internal_paths_cannot_be_written_through_preferences(workspace, interface, path):
    before = config.CONFIG_PATH.read_bytes()
    with pytest.raises(ValueError, match="solo lectura"):
        save_program_changes({"ip.workers": 7, path: "replacement"}, SettingsContext(interface))
    assert config.CONFIG_PATH.read_bytes() == before


@pytest.mark.parametrize(
    "values",
    [
        {"workers": "7", "timeout": "nan"},
        {"workers": "7", "projectSaveIntervalMinutes": "inf"},
        {"workers": "7", "serviceIdentification": "yes"},
        {"workers": "7", "workersUnknown": "1"},
        {"workers": True},
    ],
)
def test_form_batch_failure_keeps_file_byte_identical(workspace, values):
    before = config.CONFIG_PATH.read_bytes()
    with pytest.raises((ValueError, TypeError)):
        save_form_values(values, SettingsContext("tui"))
    assert config.CONFIG_PATH.read_bytes() == before


@pytest.mark.parametrize("option", ["--timeout", "--save-interval"])
def test_legacy_cli_rejects_nonfinite_values_before_any_write(workspace, option):
    before = config.CONFIG_PATH.read_bytes()
    args = cli_args("--workers", "7", option, "nan")
    with pytest.raises(ValueError, match="finito"):
        args.handler(args)
    assert config.CONFIG_PATH.read_bytes() == before


def test_direct_namespace_does_not_bypass_boolean_validation(workspace):
    args = cli_args()
    args.remote_password_auth = "yes"
    before = config.CONFIG_PATH.read_bytes()
    with pytest.raises(ValueError, match="on u off"):
        run_settings(args)
    assert config.CONFIG_PATH.read_bytes() == before


@pytest.mark.parametrize("route", ["direct", "catalog", "form", "legacy"])
def test_remote_admin_denial_precedes_config_store_and_key_creation(workspace, monkeypatch, route):
    monkeypatch.setattr("lanctl.core.local_permissions.elevated", lambda: False)
    before = config.CONFIG_PATH.read_bytes()
    with (
        patch(
            "lanctl.apps.access.service.AccessService.__init__",
            side_effect=AssertionError("store constructed"),
        ),
        pytest.raises(PermissionError),
    ):
        if route == "direct":
            set_program_value("access.remote.port", 2223)
        elif route == "catalog":
            save_program_changes(
                {"ip.workers": 7, "access.remote": {"port": 2223}}, SettingsContext("gui")
            )
        elif route == "form":
            save_form_values({"workers": "7", "remoteAccessPort": "2223"}, SettingsContext("tui"))
        else:
            args = cli_args("--workers", "7", "--remote-port", "2223")
            args.handler(args)
    assert config.CONFIG_PATH.read_bytes() == before
    assert not (config.CONFIG_PATH.parent.parent / "access").exists()


def test_legacy_backend_permission_failure_is_not_reported_as_success(workspace, monkeypatch):
    monkeypatch.setattr("lanctl.core.local_permissions.elevated", lambda: True)
    before = config.CONFIG_PATH.read_bytes()
    with (
        patch(
            "lanctl.apps.access.settings_lifecycle.remote_settings_transaction",
            side_effect=PermissionError("filesystem denied"),
        ),
        patch("lanctl.apps.ip.interfaces.cli.commands.settings.ok") as success,
        pytest.raises(PermissionError, match="filesystem denied"),
    ):
        args = cli_args("--workers", "7", "--remote-port", "2223")
        args.handler(args)
    success.assert_not_called()
    assert config.CONFIG_PATH.read_bytes() == before


def test_remote_port_conflict_is_validated_before_initialization(workspace, monkeypatch):
    from lanctl.apps.access.service import DEFAULT_CONFIG
    from lanctl.core.paths import application_path

    monkeypatch.setattr("lanctl.core.local_permissions.elevated", lambda: True)
    target = application_path(workspace["accessConfig"])
    target.parent.mkdir(parents=True)
    stored = {
        **DEFAULT_CONFIG,
        "https": {**DEFAULT_CONFIG["https"], "enabled": True, "bind": "192.168.1.3", "port": 2223},
    }
    target.write_text(json.dumps(stored))
    before = target.read_bytes(), config.CONFIG_PATH.read_bytes()
    with pytest.raises(ValueError, match="colisiona"):
        save_program_changes(
            {"access.remote": {"bind": "192.168.1.3", "cidr": "192.168.1.0/24", "port": 2223}},
            SettingsContext("cli"),
        )
    assert before == (target.read_bytes(), config.CONFIG_PATH.read_bytes())
    assert not application_path(workspace["accessUsers"]).exists()


def test_user_backend_applies_without_elevation_or_environment_mutation(workspace, monkeypatch):
    monkeypatch.setattr("lanctl.core.local_permissions.elevated", lambda: False)
    before = os.environ.get("LANCTL_DATA_SCOPE")
    save_program_changes(
        {"access.remote": {"backend": "user", "port": 2223}}, SettingsContext("gui")
    )
    assert config.load_config()["remoteAccessPort"] == 2223
    from lanctl.core.paths import application_path

    stored = json.loads(application_path(workspace["accessConfig"]).read_text())
    assert stored["ssh"]["enabled"] is False
    assert stored["ssh"]["port"] == 2223
    assert os.environ.get("LANCTL_DATA_SCOPE") == before


def test_data_scope_is_nested_and_thread_local(monkeypatch):
    from lanctl.core.paths import scoped_data_paths, service_data_scope

    monkeypatch.setenv("LANCTL_DATA_SCOPE", "service")
    with scoped_data_paths("user"):
        assert not service_data_scope()
        with ThreadPoolExecutor(1) as pool:
            assert pool.submit(service_data_scope).result()
        with scoped_data_paths("service"):
            assert service_data_scope()
        assert not service_data_scope()
    assert service_data_scope()


def test_form_key_swap_and_visibility_are_validated_as_one_batch(workspace):
    original = config.load_config()["tuiKeyBindings"]
    save_form_values(
        {"tuiKey.save": original["help"], "tuiKey.help": original["save"]},
        SettingsContext("tui"),
        visibility={"help": "off"},
    )
    saved = config.load_config()
    assert saved["tuiKeyBindings"]["save"] == original["help"]
    assert saved["tuiKeyBindings"]["help"] == original["save"]
    assert "help" not in saved["tuiFooterButtons"]


def test_remote_child_cannot_use_legacy_or_catalog_paths(workspace, monkeypatch):
    monkeypatch.setenv("LANCTL_REMOTE_SETTINGS", "1")
    before = config.CONFIG_PATH.read_bytes()
    for arguments in [
        ("--credentials", "replacement"),
        ("--set", "plugins.registry", "replacement"),
        ("--remote-backend", "user"),
        ("--projects-directory", "replacement"),
    ]:
        with pytest.raises(ValueError, match="solo lectura"):
            args = cli_args(*arguments)
            args.handler(args)
    assert config.CONFIG_PATH.read_bytes() == before
    args = cli_args("--workers", "7")
    assert args.handler(args) == 0
    assert config.load_config()["workers"] == 7


def test_remote_transport_keeps_authorization_and_sets_server_context(workspace):
    from lanctl.apps.access.remote import LanctlCommandAdapter

    auth, runner = Mock(), Mock(return_value=SimpleNamespace(returncode=0, stdout="ok", stderr=""))
    adapter = LanctlCommandAdapter(auth, runner=runner)
    assert adapter.execute("user", "settings --workers 7") == (0, "ok")
    auth.require.assert_called_once_with("user", "system.configure")
    assert runner.call_args.kwargs["env"]["LANCTL_REMOTE_SETTINGS"] == "1"
    auth.require.side_effect = PermissionError("denied")
    runner.reset_mock()
    with pytest.raises(PermissionError):
        adapter.execute("user", "settings --workers 7")
    runner.assert_not_called()


def test_catalog_uses_same_access_policy_and_remote_hides_internal_paths(workspace):
    local = {e["path"]: e for e in settings_entries(SettingsContext("gui"))}
    assert "plugins.registry" not in local
    remote = {e["path"]: e for e in settings_entries(SettingsContext("remote"))}
    assert "plugins.registry" not in remote
    assert remote["access.remote"]["readOnly"]


def test_gui_and_tui_save_without_constructing_a_cli_parser(workspace):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.apps.ip.interfaces.tui.main import LanctlTui
    from lanctl.apps.ip.interfaces.tui.modal import ModalState, SettingField
    from lanctl.apps.suite.gui import SuiteApi

    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop, suite = DesktopApi(), SuiteApi()
    with (
        patch(
            "lanctl.apps.ip.interfaces.cli.main.build_parser", side_effect=AssertionError("parser")
        ),
        patch(
            "lanctl.apps.ip.interfaces.cli.commands.settings.register_settings_command",
            side_effect=AssertionError("parser"),
        ),
    ):
        assert desktop.get_settings()["ok"]
        assert desktop.save_settings({"workers": "9", "timeout": "0.6"})["ok"]
        assert suite.save_catalog_setting("program", "ip.workers", 10)["ok"]
        assert suite.save_launcher_setting("lanip", "ip.workers", 11)["ok"]
        assert not suite.save_launcher_setting("lanrack", "ip.workers", 12)["ok"]
        assert not suite.save_launcher_setting("lanaccess", "access.users", "replacement")["ok"]
        tui = LanctlTui.__new__(LanctlTui)
        modal = ModalState(
            "settings",
            "Settings",
            ["General"],
            [[]],
            items=[SettingField("workers", "Workers", "--workers", "12", "11", "entero")],
        )
        tui.modal, tui.reload, tui._set_command_output = modal, Mock(), Mock()
        tui._save_settings(modal)
        assert tui.modal is None
        assert config.load_config()["workers"] == 12


def test_stale_tui_form_cannot_write_after_project_selection_changes(workspace):
    from lanctl.apps.ip.interfaces.tui.main import LanctlTui
    from lanctl.apps.ip.interfaces.tui.modal import ModalState, SettingField

    tui = LanctlTui.__new__(LanctlTui)
    tui._project_config = config.load_config()
    config.update_config(lambda cfg: cfg.update(database="another-project.json"))
    before = config.CONFIG_PATH.read_bytes()
    modal = ModalState(
        "settings",
        "Settings",
        ["General"],
        [[]],
        items=[SettingField("workers", "Workers", "--workers", "12", "64", "entero")],
    )
    tui.modal = modal
    tui._save_settings(modal)
    assert "proyecto cambió" in modal.footer
    assert config.CONFIG_PATH.read_bytes() == before


@pytest.mark.parametrize("scope", ["--scope project", "--sco=project"])
def test_remote_project_settings_also_require_project_permission(workspace, scope):
    from lanctl.apps.access.remote import LanctlCommandAdapter

    auth, runner = Mock(), Mock()
    auth.require.side_effect = [None, PermissionError("project.manage")]
    with pytest.raises(PermissionError, match=r"project\.manage"):
        LanctlCommandAdapter(auth, runner=runner).execute(
            "user", f"settings {scope} --set lan.name Test"
        )
    runner.assert_not_called()


def test_legacy_remote_read_does_not_disclose_internal_store_paths(workspace, monkeypatch, capsys):
    monkeypatch.setenv("LANCTL_REMOTE_SETTINGS", "1")
    args = cli_args()
    assert run_settings(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert "plugins.registry" not in result
    assert "storage.credentials" not in result
    assert result["ip.workers"] == workspace["workers"]


def test_invalid_batch_before_remote_application_and_nested_json_types(workspace, monkeypatch):
    apply = Mock()
    monkeypatch.setattr("lanctl.apps.access.settings.apply_remote_settings", apply)
    before = config.CONFIG_PATH.read_bytes()
    with pytest.raises(ValueError):
        save_program_changes(
            {"access.remote": {"backend": "user"}, "network.dnsServers": [True]},
            SettingsContext("gui"),
        )
    apply.assert_not_called()
    assert config.CONFIG_PATH.read_bytes() == before


def test_remote_child_receives_scoped_paths_without_changing_parent_environment(
    workspace, monkeypatch
):
    from lanctl.apps.access.processes import start_service_process
    from lanctl.core.paths import scoped_data_paths

    monkeypatch.setenv("LANCTL_DATA_SCOPE", "service")
    monkeypatch.setenv("LANCTL_SERVICE_MODE", "1")
    service = Mock(config_path="config.json", store=SimpleNamespace(path="users.dc"))
    process = Mock(pid=999)
    process.poll.return_value = None
    service.config.return_value = {"ssh": {}}
    with (
        patch("lanctl.apps.access.processes.platform.system", return_value="Windows"),
        patch("lanctl.apps.access.processes.subprocess.Popen", return_value=process) as spawn,
        patch("lanctl.apps.access.processes.uuid4", return_value=SimpleNamespace(hex="token")),
        patch(
            "lanctl.apps.access.runtime_state._read",
            return_value={
                "state": "starting",
                "token": "token",
                "processId": 999,
                "processIdentity": "test-identity",
            },
        ),
        patch("lanctl.apps.access.runtime_state._alive", return_value=True),
        patch("lanctl.apps.access.runtime_state._ready", return_value=True),
        scoped_data_paths("user"),
    ):
        assert start_service_process(service, "ssh") is process
    arguments = spawn.call_args.args[0]
    environment = spawn.call_args.kwargs["env"]
    assert arguments[arguments.index("--scope") + 1] == "user"
    assert environment["LANCTL_DATA_SCOPE"] == "user"
    assert "LANCTL_SERVICE_MODE" not in environment
    assert os.environ["LANCTL_DATA_SCOPE"] == "service"
    assert os.environ["LANCTL_SERVICE_MODE"] == "1"
