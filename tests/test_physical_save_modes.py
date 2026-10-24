"""Committed physical edits must apply the shared VLF policy after releasing locks."""

import io
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch
from zipfile import ZipFile

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.tui.app import LanwireTui
from lanctl.core import config
from lanctl.core.file_transaction import locked_files
from lanctl.core.projects.physical import empty_inventory, import_inventory
from lanctl.core.projects.physical_mutations import physical_mutation
from lanctl.core.projects.save_policy import save_active_project, workspace_is_dirty
from lanctl.core.projects.workspace import activate_project_workspace


def saved_inventory(project):
    with ZipFile(project) as archive:
        if "devices/physical.json" not in archive.namelist():
            return empty_inventory()
        return json.loads(archive.read("devices/physical.json"))["inventory"]


def set_mode(mode="automatic.allChanges"):
    settings = config.load_config()
    settings["projectSaveMode"] = mode
    config.save_config(settings)
    return config.load_config()


def test_wire_cli_committed_change_reaches_vlf(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    database = IDFDatabaseManager(settings["physicalDatabase"])
    result = CommandProcessor(database).execute("reserve PC-01 name=CLI")
    assert result.refresh, result
    assert saved_inventory(first)["records"]["PC-01"]["data"]["name"] == "CLI"
    assert not workspace_is_dirty(config.load_config())


@pytest.mark.parametrize(
    ("mode", "trigger", "later_saved"),
    [
        ("manual", "change", False),
        ("manual.inCloseConsult", "close", False),
        ("automatic.toClose", "close", True),
        ("automatic.toScan", "scan", True),
        ("automatic.timeToSave", "timer", True),
        ("automatic.allChanges", "change", True),
    ],
)
def test_physical_mutation_respects_each_save_mode(workspace, tmp_path, mode, trigger, later_saved):
    first, _ = projects(workspace, tmp_path)
    settings = set_mode(mode)
    database = IDFDatabaseManager(settings["physicalDatabase"])
    CommandProcessor(database).execute("reserve PC-01 name=Policy")
    immediate = mode == "automatic.allChanges"
    assert ("PC-01" in saved_inventory(first)["records"]) == immediate
    assert workspace_is_dirty(config.load_config()) != immediate
    result = save_active_project(trigger)
    assert result.saved == (later_saved and not immediate)
    assert ("PC-01" in saved_inventory(first)["records"]) == later_saved
    if not later_saved:
        assert save_active_project(force=True).saved


def test_plugin_save_policy_is_reused(workspace, tmp_path):
    from lanctl.core.projects.save_policy import SaveModeDefinition

    first, _ = projects(workspace, tmp_path)
    definition = SaveModeDefinition("Example.Save.Changes.Mode", frozenset({"change"}))
    with patch("lanctl.core.projects.save_policy._plugin_modes", return_value=[definition]):
        settings = set_mode(definition.mode)
        CommandProcessor(IDFDatabaseManager(settings["physicalDatabase"])).execute("add PC")
    assert "PC-00" in saved_inventory(first)["records"]


def test_batch_and_nested_services_save_once_after_unlock(workspace, tmp_path):
    from lanctl.apps.rack.service import RackService

    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    database = IDFDatabaseManager(settings["physicalDatabase"])
    paths = [database.path, Path(settings["database"]), Path(settings["groups"]), Path(first)]

    def check_unlocked(*args, **kwargs):
        def take_locks():
            with locked_files(paths, timeout=0.5):
                return True

        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(take_locks).result(timeout=2)
        return save_active_project(*args, **kwargs)

    with patch(
        "lanctl.core.projects.save_policy.save_active_project", side_effect=check_unlocked
    ) as save:
        result = CommandProcessor(database).execute("add PC -more 3")
        assert not result.lines[0].startswith("Error"), result
        assert save.call_count == 1
        rack = RackService(str(database.path))
        rack.edit_element(
            rack.snapshot()["organizationRevision"], "create", "", {"kind": "rack", "prefix": "RK"}
        )
        assert save.call_count == 2
    assert len(saved_inventory(first)["records"]) == 4


@pytest.mark.parametrize(
    "command",
    ["list", "show PC-01", "graph", "help", "clear", "prefix list", "idf types", "delete MISSING"],
)
def test_reads_and_rejected_edits_do_not_save_dirty_inventory(workspace, tmp_path, command):
    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    database = IDFDatabaseManager(settings["physicalDatabase"])
    database.add("PC-01", {"name": "Pending"})
    before = Path(first).read_bytes()
    with patch("lanctl.core.projects.save_policy.save_active_project") as save:
        CommandProcessor(database).execute(command)
    save.assert_not_called()
    assert Path(first).read_bytes() == before
    assert workspace_is_dirty(config.load_config())


def test_concurrent_writer_cannot_turn_a_read_into_autosave(workspace, tmp_path, monkeypatch):
    first, _ = projects(workspace, tmp_path)
    database = IDFDatabaseManager(set_mode()["physicalDatabase"])
    original = database.list

    def list_after_foreign_write(prefix=None):
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(database.add, "PC-01", {"name": "Other operation"}).result(timeout=3)
        return original(prefix)

    monkeypatch.setattr(database, "list", list_after_foreign_write)
    with patch("lanctl.core.projects.save_policy.save_active_project") as save:
        CommandProcessor(database).execute("list")
    save.assert_not_called()
    assert saved_inventory(first)["records"] == {}


def test_selection_change_during_edit_only_saves_original_project(workspace, tmp_path, monkeypatch):
    first, second = projects(workspace, tmp_path)
    database = IDFDatabaseManager(set_mode()["physicalDatabase"])
    original = database.create

    def create_then_switch(*args, **kwargs):
        # Switch while A's operation is pinned but before it commits: a switch
        # after committing is correctly blocked by the dirty-workspace guard.
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(activate_project_workspace, second).result(timeout=5)
        return original(*args, **kwargs)

    monkeypatch.setattr(database, "create", create_then_switch)
    result = CommandProcessor(database).execute("add PC")
    assert not result.lines[0].startswith("Error"), result
    assert config.load_config()["activeProject"] == second
    assert "PC-00" in saved_inventory(first)["records"]
    assert saved_inventory(second)["records"] == {}


def test_external_database_does_not_save_active_project(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    set_mode()
    before = Path(first).read_bytes()
    database = IDFDatabaseManager(tmp_path / "external.db")
    with patch("lanctl.core.projects.save_policy.save_active_project") as save:
        CommandProcessor(database).execute("add PC")
    save.assert_not_called()
    assert database.get("PC-00")
    assert Path(first).read_bytes() == before


def test_global_database_without_project_keeps_legacy_behavior(workspace):
    settings = set_mode()
    database = IDFDatabaseManager(settings["physicalDatabase"])
    with patch("lanctl.core.projects.save_policy.save_active_project") as save:
        CommandProcessor(database).execute("add PC")
    save.assert_not_called()
    assert database.get("PC-00")


def test_failed_vlf_save_keeps_edit_and_reports_original_error(workspace, tmp_path):
    from lanctl.core.errors import errors

    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    database = IDFDatabaseManager(settings["physicalDatabase"])
    before = Path(first).read_bytes()
    with (
        patch("lanctl.core.projects.vlf.update_project", side_effect=OSError("test disk full")),
        patch.object(errors, "from_exception", wraps=errors.from_exception) as report,
    ):
        result = CommandProcessor(database).execute("add PC")
    assert result.refresh and result.lines[0].startswith("Error"), result
    assert "No repitas la edición" in result.lines[0]
    assert database.get("PC-00")
    assert Path(first).read_bytes() == before
    assert workspace_is_dirty(config.load_config())
    reports = [
        call
        for call in report.call_args_list
        if call.kwargs.get("origin") == "LANCTL.Project.Physical.Autosave"
    ]
    assert len(reports) == 1 and isinstance(reports[0].args[0], OSError)
    assert reports[0].kwargs["details"]["changesCommitted"] is True
    assert save_active_project(force=True).saved
    assert "PC-00" in saved_inventory(first)["records"]


def test_partial_batch_keeps_error_and_saves_committed_records(workspace, tmp_path, monkeypatch):
    first, _ = projects(workspace, tmp_path)
    database = IDFDatabaseManager(set_mode()["physicalDatabase"])
    original = database.create

    def fail_second(*args, **kwargs):
        if database.all():
            raise ValueError("test second item rejected")
        return original(*args, **kwargs)

    monkeypatch.setattr(database, "create", fail_second)
    result = CommandProcessor(database).execute("add PC -more 2")
    assert result.lines[0].startswith("Error"), result
    assert result.refresh
    assert set(saved_inventory(first)["records"]) == {"PC-00"}


def test_original_operation_error_is_not_hidden_by_save_error(workspace, tmp_path):
    projects(workspace, tmp_path)
    database = IDFDatabaseManager(set_mode()["physicalDatabase"])
    with (
        patch("lanctl.core.projects.vlf.update_project", side_effect=OSError("save failed")),
        pytest.raises(ValueError, match="original failure"),
        physical_mutation(database.path),
    ):
        database.add("PC-01")
        raise ValueError("original failure")
    assert workspace_is_dirty(config.load_config())


def test_concurrent_commands_keep_both_commits(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    ready = Barrier(2)

    def save_after_both_commits(*args, **kwargs):
        ready.wait(timeout=5)
        return save_active_project(*args, **kwargs)

    def command(identifier):
        processor = CommandProcessor(IDFDatabaseManager(settings["physicalDatabase"]))
        return processor.execute(f"reserve {identifier}")

    with (
        patch(
            "lanctl.core.projects.save_policy.save_active_project",
            side_effect=save_after_both_commits,
        ),
        ThreadPoolExecutor(max_workers=2) as pool,
    ):
        futures = [pool.submit(command, identifier) for identifier in ("PC-01", "PC-02")]
        results = [future.result(timeout=10) for future in futures]
    assert all(not result.lines[0].startswith("Error") for result in results), results
    assert set(saved_inventory(first)["records"]) == {"PC-01", "PC-02"}
    assert not workspace_is_dirty(config.load_config())


def test_gui_and_cpd_services_use_single_shared_policy_call(workspace, tmp_path):
    from lanctl.apps.rack.service import RackService

    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    wire = api("lanwire")
    with patch(
        "lanctl.core.projects.save_policy.save_active_project", wraps=save_active_project
    ) as save:
        created = wire.wire_create({"kind": "rack", "prefix": "RK"})
        assert created["ok"], created
        assert save.call_count == 1
        wire_room = wire.wire_organization(
            wire.bootstrap()["organizationRevision"], "create", {"name": "Wire room"}
        )
        assert wire_room["ok"], wire_room
        assert save.call_count == 2
        rack = RackService(settings["physicalDatabase"])
        room = rack.organize(rack.snapshot()["organizationRevision"], "create", {"name": "Main"})
        assert save.call_count == 3
    assert room["id"] in saved_inventory(first)["cpdOrganization"]["rooms"]
    assert wire_room["id"] in saved_inventory(first)["cpdOrganization"]["rooms"]


def test_explicit_import_uses_policy_and_preserves_source(workspace, tmp_path):
    from lanctl.core.project_context import project_identity

    source = IDFDatabaseManager(tmp_path / "legacy.db")
    source.add("PC-01")
    original = source.path.read_bytes()
    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    import_inventory(source.path, project_identity(settings))
    assert "PC-01" in saved_inventory(first)["records"]
    assert source.path.read_bytes() == original


def test_tui_save_failure_keeps_interface_and_pending_changes(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    database = IDFDatabaseManager(config.load_config()["physicalDatabase"])
    database.add("PC-01", {"type": "device.pc", "name": "TUI", "ports": {}})
    save_active_project(force=True)
    set_mode()
    tui = LanwireTui(database.path, stream=io.StringIO())
    with patch("lanctl.core.projects.vlf.update_project", side_effect=OSError("test disk full")):
        tui.handle_key("DELETE")
        tui.handle_key("ENTER")
    assert tui.running
    assert database.get("PC-01") is None
    assert "PC-01" in saved_inventory(first)["records"]
    assert any("No repitas la edición" in line for line in tui.messages)
    assert workspace_is_dirty(config.load_config())


def test_tui_field_and_port_edits_reach_vlf(workspace, tmp_path):
    from lanctl.apps.wire.topology import build_new_idf_data

    first, _ = projects(workspace, tmp_path)
    database = IDFDatabaseManager(config.load_config()["physicalDatabase"])
    database.add("PC-01", build_new_idf_data("pc.1port"))
    save_active_project(force=True)
    set_mode()
    tui = LanwireTui(database.path, stream=io.StringIO())
    tui.view_id = "PC-01"
    tui.modal_focus = "editor"
    tui.editor_selection = next(
        i
        for i, field in enumerate(tui._editing_fields(tui._modal_record()))
        if field.label == "name"
    )
    tui.editor_buffer = "Renamed in TUI"
    tui.handle_key("ENTER")
    assert saved_inventory(first)["records"]["PC-01"]["data"]["name"] == "Renamed in TUI"
    tui.editor_scope = "port"
    tui.modal_selection = 0
    tui.editor_selection = 0
    tui.editor_buffer = "UPLINK"
    tui.handle_key("ENTER")
    assert "UPLINK" in saved_inventory(first)["records"]["PC-01"]["data"]["ports"]


def test_wire_cli_reports_nonzero_after_failed_autosave(workspace, tmp_path, capsys):
    from lanctl.apps.wire.cli.main import main

    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    with patch("lanctl.core.window_icons.apply_terminal_icon"):
        assert main(["reserve", "PC-01", "name=CLI"]) == 0
        with patch(
            "lanctl.core.projects.vlf.update_project", side_effect=OSError("test disk full")
        ):
            assert main(["reserve", "PC-02", "name=Pending"]) == 1
    assert set(saved_inventory(first)["records"]) == {"PC-01"}
    assert IDFDatabaseManager(settings["physicalDatabase"]).get("PC-02")
    assert "No repitas la edición" in capsys.readouterr().out


def test_rack_cli_creation_and_dimensions_apply_policy(workspace, tmp_path, capsys):
    from lanctl.apps.rack.cli import main

    first, _ = projects(workspace, tmp_path)
    settings = set_mode()
    with patch("lanctl.core.window_icons.apply_terminal_icon"):
        assert main(["add-element", "--kind", "rack", "--prefix", "RK"]) == 0
        identifier = next(iter(saved_inventory(first)["records"]))
        assert main(["dimensions", identifier, "--units", "24", "--width-inches", "19"]) == 0
        with patch(
            "lanctl.core.projects.vlf.update_project", side_effect=OSError("test disk full")
        ):
            assert main(["dimensions", identifier, "--units", "22", "--width-inches", "19"]) == 1
    assert saved_inventory(first)["records"][identifier]["data"]["units"] == 24
    assert IDFDatabaseManager(settings["physicalDatabase"]).get(identifier)["data"]["units"] == 22
    assert "No repitas la edición" in capsys.readouterr().out


def test_wire_tui_delete_reaches_vlf(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    settings = config.load_config()
    database = IDFDatabaseManager(settings["physicalDatabase"])
    database.add("PC-01", {"type": "device.pc", "name": "TUI", "ports": {}})
    save_active_project(force=True)
    set_mode()
    tui = LanwireTui(database.path, stream=io.StringIO())
    tui.handle_key("DELETE")
    tui.handle_key("ENTER")
    assert database.get("PC-01") is None
    assert saved_inventory(first)["records"] == {}
    assert not workspace_is_dirty(config.load_config())
