"""P69: interface/launcher isolation without changing persistence or permissions."""

import argparse
import json
from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.apps.ip.interfaces.cli.commands.settings import register_settings_command
from lanctl.apps.suite.settings import (
    cli_context,
    save_form_values,
    save_program_changes,
    save_setting,
    settings_entries,
)
from lanctl.core import config
from lanctl.core.settings_catalog import leaves
from lanctl.core.settings_policy import SettingsContext, prepare_program_changes


def arguments(*options):
    parser = argparse.ArgumentParser()
    register_settings_command(parser.add_subparsers())
    return parser.parse_args(["settings", *options])


@pytest.mark.parametrize("interface", ["cli", "tui", "gui", "remote"])
@pytest.mark.parametrize(
    "launcher", ["lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"]
)
def test_read_write_matrix(workspace, subtests, interface, launcher):
    context = SettingsContext(interface, launcher)
    current = config.load_config()
    defaults = dict(leaves(config.DOCUMENT_DEFAULTS))
    visible = {entry["path"] for entry in settings_entries(context)}
    effective = "cli" if interface == "remote" else interface
    # Independent examples of common, interface-only, shared-terminal and domain rules.
    for path, interfaces, launchers in [
        ("startup.interface", {"cli", "tui", "gui"}, None),
        ("projects.saveMode", {"cli", "tui", "gui"}, None),
        ("localization.language", {"cli", "tui", "gui"}, None),
        ("logging.retentionDays", {"cli", "tui", "gui"}, None),
        ("cli.commandChaining", {"cli"}, None),
        ("gui.density", {"gui"}, None),
        ("startup.closeGuiOnLaunch", {"gui"}, {"lanctl"}),
        ("tui.panelLayout", {"tui"}, {"lanip"}),
        ("tui.keyBindings.save", {"tui"}, {"lanip"}),
        ("ip.listColumns", {"cli", "tui"}, {"lanip"}),
        ("ip.progress", {"cli"}, {"lanip"}),
        ("ip.workers", {"cli", "tui", "gui"}, {"lanip"}),
        ("wol.method", {"cli", "tui", "gui"}, {"lanip"}),
        ("monitor.execution.workers", {"cli", "tui", "gui"}, {"lanmon"}),
        ("network.range", {"cli", "tui", "gui"}, {"lanip", "lanmon"}),
    ]:
        allowed = effective in interfaces and (
            launchers is None or launcher == "lanctl" or launcher in launchers
        )
        with subtests.test(path=path):
            assert (path in visible) == allowed
            if allowed:
                prepare_program_changes(current, {path: defaults[path]}, context)
            else:
                with pytest.raises(ValueError, match="solo lectura"):
                    prepare_program_changes(current, {path: defaults[path]}, context)


@pytest.mark.parametrize("interface", ["cli", "tui", "gui", "remote"])
def test_catalog_never_exposes_internal_or_future_unknown_fields(workspace, interface):
    def extend(cfg):
        cfg.document["access"]["remote"]["futureSecret"] = "DO-NOT-EXPOSE"
        cfg.document["gui"]["futureSetting"] = "unreviewed"

    config.update_config(extend)
    entries = settings_entries(SettingsContext(interface))
    serialized = json.dumps(entries)
    for token in [
        "DO-NOT-EXPOSE",
        "futureSetting",
        "schemaVersion",
        "workspace.",
        "settingsDownloadedAt",
    ]:
        assert token not in serialized
    paths = {entry["path"] for entry in entries}
    assert not paths & {
        "storage.credentials",
        "plugins.registry",
        "access.users",
        "projects.active",
    }
    before = config.CONFIG_PATH.read_bytes()
    with pytest.raises(ValueError):
        save_program_changes({"gui.futureSetting": "unsafe"}, SettingsContext(interface))
    assert config.CONFIG_PATH.read_bytes() == before


@pytest.mark.parametrize(
    "context,changes",
    [
        (SettingsContext("gui"), {"ip.workers": 7, "cli.commandChaining": False}),
        (SettingsContext("tui"), {"ip.workers": 7, "startup.closeGuiOnLaunch": True}),
        (SettingsContext("cli"), {"ip.workers": 7, "tui.panelLayout": "cli.top"}),
        (SettingsContext("gui", "lanrack"), {"logging.retentionDays": 7, "ip.workers": 7}),
    ],
)
def test_rejected_batch_has_no_storage_or_remote_side_effects(workspace, context, changes):
    before = config.CONFIG_PATH.read_bytes()
    with patch("lanctl.apps.access.settings_lifecycle.remote_settings_transaction") as remote:
        with pytest.raises(ValueError, match="solo lectura"):
            save_program_changes(changes, context)
        remote.assert_not_called()
    assert config.CONFIG_PATH.read_bytes() == before


def test_allowed_changes_preserve_other_interfaces_and_unknown_persistent_metadata(workspace):
    original = config.canonical_config(config.load_config())
    original["tui"]["panelLayout"] = "cli.top"
    original["cli"]["commandChaining"] = False
    original["customExtension"] = {"opaque": [1, 2, 3]}
    config.save_config(config.config_from_document(original))
    save_program_changes({"gui.density": "compact", "ip.workers": 11}, SettingsContext("gui"))
    saved = config.canonical_config(config.load_config())
    assert saved["tui"] == original["tui"]
    assert saved["cli"] == original["cli"]
    assert saved["customExtension"] == original["customExtension"]
    save_program_changes({"cli.commandChaining": True}, SettingsContext("cli"))
    assert config.canonical_config(config.load_config())["gui"]["density"] == "compact"


def test_gui_adapters_filter_and_reject_spoofed_context_and_cross_interface_fields(workspace):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.apps.suite.gui import SuiteApi
    from lanctl.apps.suite.launcher_gui import LauncherApi

    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop, suite, rack = DesktopApi(), SuiteApi(), LauncherApi("lanrack")
    for adapter in [desktop, suite]:
        fields = {field["key"] for field in adapter.get_settings()["fields"]}
        assert "cliCommandChaining" not in fields
        assert "workers" in fields
        before = config.CONFIG_PATH.read_bytes()
        assert not adapter.save_settings({"workers": "7", "cliCommandChaining": "off"})["ok"]
        assert not adapter.save_settings({"interface": "cli", "workers": "7"})["ok"]
        assert config.CONFIG_PATH.read_bytes() == before
    assert "closeGuiOnLaunch" not in {f["key"] for f in desktop.get_settings()["fields"]}
    assert "closeGuiOnLaunch" in {f["key"] for f in suite.get_settings()["fields"]}
    assert not desktop.save_settings({"closeGuiOnLaunch": "on"})["ok"]
    assert suite.save_settings({"closeGuiOnLaunch": "on"})["ok"]
    for launcher in ["lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon", "cli"]:
        assert not suite.save_launcher_setting(launcher, "cli.commandChaining", False)["ok"]
    before = config.CONFIG_PATH.read_bytes()
    assert not rack.save_setting("ip.workers", 8)["ok"]
    assert "ip.workers" not in {entry["path"] for entry in rack.settings()["entries"]}
    assert config.CONFIG_PATH.read_bytes() == before


def test_tui_fields_and_direct_save_reject_other_interface_preferences(workspace):
    from lanctl.apps.ip.interfaces.tui.main import LanctlTui
    from lanctl.apps.ip.interfaces.tui.modal import ModalState, SettingField

    tui = LanctlTui.__new__(LanctlTui)
    tui._last_screen_lines, tui.modal = [], None
    tui.show_settings()
    fields = {field.key for field in tui.modal.items}
    assert {"tuiPanelLayout", "listColumns", "workers"} <= fields
    assert not fields & {
        "closeGuiOnLaunch",
        "cliCommandChaining",
        "cliPromptSaveOnCommandExit",
        "progress",
        "database",
    }
    before = config.CONFIG_PATH.read_bytes()
    modal = ModalState(
        "settings",
        "Settings",
        ["General"],
        [[]],
        items=[
            SettingField("workers", "Workers", "--workers", "9", "64", "entero"),
            SettingField("closeGuiOnLaunch", "GUI", "--close-gui-on-launch", "on", "off", "bool"),
        ],
    )
    tui.modal = modal
    tui._save_settings(modal)
    assert "ERROR" in modal.footer
    assert config.CONFIG_PATH.read_bytes() == before
    save_form_values({"listColumns": "ip,alias"}, SettingsContext("tui"))
    assert config.load_config()["listColumns"] == ["ip", "alias"]


def test_cli_catalog_and_plain_read_only_show_cli_and_common_preferences(workspace, capsys):
    for options in [(), ("--catalog",)]:
        args = arguments(*options)
        assert args.handler(args) == 0
        output = capsys.readouterr().out
        for token in [
            "panelLayout",
            "fontScale",
            "closeGuiOnLaunch",
            "credentials",
            "schemaVersion",
        ]:
            assert token not in output
        assert "commandChaining" in output
    for option in ["--get", "--set"]:
        options = (option, "gui.density") + (("compact",) if option == "--set" else ())
        with pytest.raises(ValueError):
            args = arguments(*options)
            args.handler(args)


def test_explicit_local_cli_compatibility_options_remain_atomic(workspace):
    args = arguments("--tui-layout", "cli.top", "--close-gui-on-launch", "on", "--workers", "10")
    assert args.handler(args) == 0
    current = config.load_config()
    assert current["tuiPanelLayout"] == "cli.top"
    assert current["closeGuiOnLaunch"] is True
    assert current["workers"] == 10
    before = config.CONFIG_PATH.read_bytes()
    args = arguments("--tui-key", "save=F1", "--workers", "11")
    with pytest.raises(ValueError):
        args.handler(args)
    assert config.CONFIG_PATH.read_bytes() == before


@pytest.mark.parametrize(
    "options", [("--tui-layout", "cli.bottom"), ("--close-gui-on-launch", "off")]
)
def test_remote_cli_cannot_use_interface_compatibility_even_for_unchanged_values(
    workspace, monkeypatch, options
):
    monkeypatch.setenv("LANCTL_REMOTE_SETTINGS", "1")
    before = config.CONFIG_PATH.read_bytes()
    args = arguments(*options)
    with pytest.raises(ValueError, match="solo lectura"):
        args.handler(args)
    assert config.CONFIG_PATH.read_bytes() == before


def test_embedded_cli_keeps_cli_context_even_inside_gui_session(workspace):
    from lanctl.core.session import bind_session

    with bind_session(SimpleNamespace(launcher="lanctl", mode="gui")):
        assert cli_context().interface == "cli"
    assert cli_context().interface == "cli"


@pytest.mark.parametrize(
    "options",
    [
        ("--remote-backend", "service"),
        ("--remote-access", "off"),
        ("--remote-port", "2222"),
    ],
)
def test_remote_noop_cannot_enter_privileged_backend(workspace, monkeypatch, options):
    monkeypatch.setenv("LANCTL_REMOTE_SETTINGS", "1")
    before = config.CONFIG_PATH.read_bytes()
    with patch("lanctl.apps.access.settings_lifecycle.remote_settings_transaction") as remote:
        with pytest.raises(ValueError, match="solo lectura"):
            args = arguments(*options)
            args.handler(args)
        remote.assert_not_called()
    assert config.CONFIG_PATH.read_bytes() == before


@pytest.mark.parametrize("interface", ["cli", "tui", "gui"])
def test_project_preferences_remain_shared_without_exposing_identity_or_inventory(
    workspace, tmp_path, interface
):
    from lanctl.core.projects.settings import project_settings
    from lanctl.core.projects.vlf import create_project, verify_project

    target = tmp_path / "shared.vlf"
    create_project(target, config=workspace, name="Shared")
    original_id = project_settings(target)["identity"]["id"]
    for launcher in ["lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"]:
        context = SettingsContext(interface, launcher, "project")
        entries = {entry["path"] for entry in settings_entries(context, project_path=target)}
        assert {"identity.name", "network.cidr", "vlan.managementVlan"} <= entries
        assert not entries & {
            "identity.id",
            "identity.contentHash",
            "network.netmask",
            "vlan.vlans",
        }
        save_setting(context, "lan.description", launcher, project_path=target)
        assert project_settings(target)["lan"]["description"] == launcher
        with pytest.raises(ValueError):
            save_setting(context, "identity.id", "replacement", project_path=target)
    assert project_settings(target)["identity"]["id"] == original_id
    verify_project(target)


@pytest.mark.parametrize(
    "invalid",
    [
        {"gui.density": "compact"},
        {"schemaVersion": 9},
        {"confirmExit": "false"},
        {"cliHeight": True},
        {"cliHeight": 100},
        {"columnWidths": {"ip": 12}},
        {"columnWidths": {"name": 1}},
        {"panelLayout": []},
        {"tableDensity": "invalid"},
    ],
)
def test_wire_tui_rejects_cross_launcher_and_invalid_batches(
    workspace, tmp_path, monkeypatch, invalid
):
    from lanctl.apps.wire.tui import settings

    target = tmp_path / "wire-tui.config"
    monkeypatch.setattr(settings, "settings_path", lambda: target)
    settings.save_settings(deepcopy(settings.DEFAULT_SETTINGS))
    before = target.read_bytes(), config.CONFIG_PATH.read_bytes()
    with pytest.raises(ValueError):
        settings.save_settings({"showGroups": False, **invalid})
    assert before == (target.read_bytes(), config.CONFIG_PATH.read_bytes())


def test_wire_tui_saves_its_own_preferences_without_affecting_lanip(
    workspace, tmp_path, monkeypatch
):
    from lanctl.apps.wire.tui import settings

    target = tmp_path / "wire-tui.config"
    monkeypatch.setattr(settings, "settings_path", lambda: target)
    before = config.CONFIG_PATH.read_bytes()
    settings.save_settings({"panelLayout": "cli.top", "columnWidths": {"name": 24}})
    assert settings.load_settings()["panelLayout"] == "cli.top"
    assert settings.load_settings()["columnWidths"]["name"] == 24
    assert (
        settings.load_settings()["columnWidths"]["idf"]
        == settings.DEFAULT_SETTINGS["columnWidths"]["idf"]
    )
    assert config.CONFIG_PATH.read_bytes() == before
