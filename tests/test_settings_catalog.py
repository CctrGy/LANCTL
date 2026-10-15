import argparse
import json
import zipfile
from copy import deepcopy

import pytest

from lanctl.apps.ip.interfaces.cli.commands import settings_menu
from lanctl.apps.ip.interfaces.cli.commands.settings import register_settings_command
from lanctl.core import config
from lanctl.core.projects.settings import project_settings, update_project_setting
from lanctl.core.projects.vlf import create_project, update_project, verify_project
from lanctl.core.settings_catalog import catalog, leaves, set_program_value


@pytest.fixture
def settings_file(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_PATH", target)
    return target


def parser():
    result = argparse.ArgumentParser()
    register_settings_command(result.add_subparsers())
    return result


def test_catalog_covers_every_schema_leaf():
    entries = catalog(deepcopy(config.DOCUMENT_DEFAULTS))
    assert {entry["path"] for entry in entries} == set(dict(leaves(config.DOCUMENT_DEFAULTS)))
    assert all(entry["category"] in settings_menu.CATEGORIES for entry in entries)


def test_generic_save_preserves_session_compatible_document(settings_file):
    set_program_value("monitor.intervals.fullScan", 3600)
    set_program_value("wol.port", 7)
    set_program_value("network.dnsServers", ["1.1.1.1", "8.8.8.8"])
    saved = json.loads(settings_file.read_text(encoding="utf-8"))
    assert saved["monitor"]["intervals"]["fullScan"] == 3600
    assert saved["wol"]["port"] == 7
    assert config.load_config()["dnsServers"] == ["1.1.1.1", "8.8.8.8"]
    assert saved["ip"]["workers"] == config.DOCUMENT_DEFAULTS["ip"]["workers"]


@pytest.mark.parametrize(
    ("path", "value"),
    [
        ("ip.workers", 0),
        ("ip.workers", True),
        ("wol.port", 65536),
        ("ip.timeout", float("nan")),
        ("network.dnsServers", ["broken"]),
        ("ip.discovery", "invalid"),
        ("monitor.retention.events", "forever"),
        ("schemaVersion", 100),
        ("projects.active", "missing.vlf"),
        ("unknown.setting", "value"),
        ("tui.keyBindings.save", "INVALID"),
    ],
)
def test_invalid_settings_never_write(settings_file, path, value):
    with pytest.raises((ValueError, TypeError)):
        set_program_value(path, value)
    assert not settings_file.exists()


def test_catalog_filter_and_set_cli(settings_file, capsys):
    args = parser().parse_args(["settings", "--catalog", "--category", "monitor"])
    assert args.handler(args) == 0
    output = capsys.readouterr().out
    assert "monitor.execution.workers" in output
    assert "wol.port" not in output
    args = parser().parse_args(["settings", "--set", "cli.commandChaining", "false"])
    assert args.handler(args) == 0
    args = parser().parse_args(["settings", "--get", "cli.commandChaining"])
    capsys.readouterr()
    assert args.handler(args) == 0
    assert capsys.readouterr().out.strip() == "false"


def test_menu_navigation_edits_and_returns(settings_file, monkeypatch):
    answers = iter(["1", "8", "1", "12", "0", "0", "0"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    assert settings_menu.configuration_menu() == 0
    assert config.load_config()["workers"] == 12


def test_remote_settings_use_existing_backend(monkeypatch):
    from lanctl.apps.ip.interfaces.cli.commands import settings

    calls = []
    monkeypatch.setattr(settings, "run_settings", lambda args: calls.append(args))
    settings_menu._set(
        "program", "access.remote", '{"bind":"192.168.1.2","cidr":"192.168.1.0/24","enabled":true}'
    )
    assert calls[0].remote_bind == "192.168.1.2"
    assert calls[0].remote_cidr == "192.168.1.0/24"
    assert calls[0].remote_access == "on"


@pytest.fixture
def project(tmp_path, settings_file):
    path = tmp_path / "example.vlf"
    settings = {
        "database": str(tmp_path / "devices.json"),
        "groups": str(tmp_path / "groups.json"),
        "credentials": str(tmp_path / "credentials"),
        "range": "192.168.50.0/24",
    }
    create_project(path, config=settings, name="Original")
    return path, settings


def test_project_edits_preserve_inventory_identity_and_checksums(project):
    path, settings = project
    with zipfile.ZipFile(path) as archive:
        inventory = archive.read("devices/elements.db")
    original_id = project_settings(path)["identity"]["id"]
    update_project_setting(path, "identity", "name", "New name")
    update_project_setting(path, "lan", "description", "")
    update_project_setting(path, "network", "cidr", "10.12.0.0/16")
    update_project_setting(path, "network", "dns", ["1.1.1.1"])
    update_project_setting(path, "vlan", "managementVlan", 20)
    verify_project(path)
    with zipfile.ZipFile(path) as archive:
        assert archive.read("devices/elements.db") == inventory
    update_project(path, config=settings)
    verify_project(path)
    documents = project_settings(path)
    assert documents["identity"]["id"] == original_id
    assert documents["identity"]["name"] == "New name"
    assert documents["network"]["cidr"] == "10.12.0.0/16"
    assert documents["network"]["netmask"] == "255.255.0.0"
    assert documents["network"]["dns"] == ["1.1.1.1"]
    assert documents["vlan"]["managementVlan"] == 20
    assert list((path.parent / ".lanctl-backups").glob("*.vlf"))


def test_project_cli_reads_and_edits_active_project(project, monkeypatch, capsys):
    path, _ = project
    monkeypatch.setattr(settings_menu, "_project", lambda: path)
    args = parser().parse_args(
        ["settings", "--scope", "project", "--set", "lan.company", "Example"]
    )
    assert args.handler(args) == 0
    assert project_settings(path)["lan"]["company"] == "Example"
    args = parser().parse_args(["settings", "--scope", "project", "--catalog"])
    assert args.handler(args) == 0
    assert "identity.id" in capsys.readouterr().out
    before = path.read_bytes()
    with pytest.raises(ValueError):
        update_project_setting(path, "identity", "id", "replacement")
    with pytest.raises(ValueError):
        update_project_setting(path, "vlan", "nativeVlan", True)
    assert before == path.read_bytes()


def test_unmapped_fields_survive_session_load_and_save(settings_file):
    from threading import RLock
    from types import SimpleNamespace

    from lanctl.core.session import PROJECT_KEYS, bind_session

    settings = config.load_config()
    session = SimpleNamespace(
        lock=RLock(),
        resources=set(),
        config={key: settings.get(key) for key in PROJECT_KEYS},
        emit=lambda *args: None,
    )
    with bind_session(session):
        set_program_value("projects.workspace.directory", "custom/workspace")
        set_program_value("ip.workers", 14)
        set_program_value("tui.keyBindings.save", None)
        set_program_value("projects.saveIntervalMinutes", 0.5)
        document = config.canonical_config(config.load_config())
        assert document["projects"]["workspace"]["directory"] == "custom/workspace"
        assert document["ip"]["workers"] == 14
        assert document["tui"]["keyBindings"]["save"] is None
        assert document["projects"]["saveIntervalMinutes"] == 0.5


def test_project_network_preferences_apply_on_activation_without_losing_pending_data(
    project, settings_file, tmp_path
):
    from lanctl.core.projects.workspace import activate_project_workspace

    path, settings = project
    update_project_setting(path, "network", "cidr", "10.12.0.0/16")
    workspace = activate_project_workspace(path, config=settings, root=tmp_path / "workspaces")
    assert config.load_config()["range"] == "10.12.0.0/16"
    pending = workspace.database.read_bytes() + b"\n"
    workspace.database.write_bytes(pending)
    update_project_setting(path, "network", "scanProfile", "accurate")
    assert config.load_config()["scanProfile"] == "accurate"
    assert workspace.database.read_bytes() == pending


def test_legacy_error_level_option_is_applied(settings_file, monkeypatch):
    from lanctl.apps.ip.interfaces.cli.commands import settings

    monkeypatch.setattr(settings, "CONFIG_PATH", settings_file)
    args = parser().parse_args(["settings", "--error-log-level", "15"])
    assert args.handler(args) == 0
    assert config.load_config()["errorLogLevel"] == 15


def test_monitor_domain_validation_prevents_unusable_settings(settings_file):
    for path, value in [
        ("monitor.execution.workers", 129),
        ("monitor.intervals.networkDiscovery", 1),
        ("monitor.retention.rawSamples", "400d"),
    ]:
        with pytest.raises(ValueError):
            set_program_value(path, value)
    assert not settings_file.exists()


def test_monitor_temporary_mode_keeps_duration(settings_file):
    set_program_value("monitor.duration", "10m")
    set_program_value("monitor.mode", "temporary")
    settings = config.load_config()
    assert settings["monitor"]["duration"] == 600
    assert settings["monitor"]["mode"] == "temporary"
