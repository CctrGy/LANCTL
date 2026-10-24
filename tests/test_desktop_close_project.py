"""P80: close decisions must respect shared data and the outer save policy."""

from contextlib import ExitStack
from pathlib import Path
from unittest.mock import Mock

import pytest
from test_desktop_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.core import config
from lanctl.core.coordination import Coordinator
from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.save_policy import workspace_is_dirty
from lanctl.core.projects.workspace import prepare_project_workspace
from lanctl.core.session import Session, bind_session


@pytest.mark.parametrize("decision", ["save", "discard", "cancel"])
@pytest.mark.parametrize("peer", ["none", "same", "different"])
def test_close_decisions_preserve_other_sessions(workspace, tmp_path, decision, peer):
    first, second = projects(workspace, tmp_path)
    coordinator = Coordinator()
    with ExitStack() as stack:
        owner = Session("lanip", "gui", config.load_config(), coordinator=coordinator)
        stack.callback(owner.close)
        owner.stop_event.set()
        owner.thread.join()
        if peer != "none":
            other_config = dict(config.load_config())
            other_config["activeProject"] = first if peer == "same" else second
            other = Session("lanwire", "gui", other_config, coordinator=coordinator)
            stack.callback(other.close)
            other.stop_event.set()
            other.thread.join()
        with bind_session(owner):
            database = DeviceDatabase(config.load_config()["database"])
            device = database.upsert([{"MAC": "02:00:00:00:00:10", "IP": "192.0.2.10"}])[0]
            instance = api()
            instance._window = Mock()
            assert instance.update_device(device.device_id, {"idf": "PC-001"})["ok"]
            assert instance.project_state()["shared"] is (peer == "same")
            # Edits append their own audit to the archive. Measure only the
            # close operation, which must not implicitly save the inventory.
            archive_before = Path(first).read_bytes()
            result = instance.request_close(decision)
            assert result["ok"], result
            if decision == "cancel":
                assert not result["closed"]
                instance._window.destroy.assert_not_called()
                assert workspace_is_dirty(config.load_config())
            else:
                assert result["closed"]
                instance._window.destroy.assert_called_once()
                if decision == "discard":
                    assert result["sharedChangesRetained"] is (peer == "same")
            if decision == "save":
                assert not workspace_is_dirty(config.load_config())
                reopened = prepare_project_workspace(first, root=tmp_path / "reopened")
                assert (
                    DeviceDatabase(str(reopened.database)).resolve(device.device_id).idf == "PC-001"
                )
            else:
                assert Path(first).read_bytes() == archive_before
                if peer == "same" or decision == "cancel":
                    assert database.resolve(device.device_id).idf == "PC-001"
                else:
                    assert database.load() == []


def test_discard_uses_the_actual_custom_workspace_root(workspace, tmp_path):
    from lanctl.core.projects.workspace import activate_project_workspace

    first, _ = projects(workspace, tmp_path)
    custom = activate_project_workspace(first, root=tmp_path / "custom-workspaces")
    database = DeviceDatabase(str(custom.database))
    database.upsert([{"MAC": "02:00:00:00:00:10", "IP": "192.0.2.10"}])
    instance = api()
    instance._window = Mock()
    result = instance.request_close("discard")
    assert result["ok"] and result["closed"], result
    assert database.load() == []
    assert config.load_config()["database"] == str(custom.database)


def test_failed_native_close_does_not_bypass_the_next_close_dialog(workspace):
    instance = api()
    instance._window = Mock()
    instance._window.destroy.side_effect = RuntimeError("native close failed")
    result = instance.request_close("discard")
    assert not result["ok"]
    assert instance._closing is False


@pytest.mark.parametrize("decision", ["save", "discard"])
def test_cli_wrapper_does_not_save_a_different_project_after_gui_close(
    workspace, tmp_path, monkeypatch, decision
):
    from lanctl.apps.ip.interfaces.cli.main import main
    from lanctl.core.projects.workspace import activate_project_workspace

    _, second = projects(workspace, tmp_path)
    cfg = config.load_config()
    cfg.update(pluginSafeMode=True, projectSaveMode="automatic.toClose")
    config.save_config(cfg)
    database = DeviceDatabase(cfg["database"])
    database.upsert([{"MAC": "02:00:00:00:00:10", "IP": "192.0.2.10"}])
    before_second = Path(second).read_bytes()

    def gui_lifecycle():
        instance = api()
        instance._window = Mock()
        result = instance.request_close(decision)
        assert result["ok"] and result["closed"], result
        # Another session switches immediately after the window closes.
        activate_project_workspace(second)
        current = config.load_config()
        current["projectSaveMode"] = "automatic.toClose"
        config.save_config(current)
        DeviceDatabase(current["database"]).upsert(
            [{"MAC": "02:00:00:00:00:20", "IP": "192.0.2.20"}]
        )
        return 0

    monkeypatch.setattr("lanctl.apps.ip.interfaces.gui.desktop.run_gui", gui_lifecycle)
    assert main(["--gui"]) == 0
    assert workspace_is_dirty(config.load_config())
    # Database audit logs may change; the saved inventory must remain empty.
    from io import BytesIO
    from zipfile import ZipFile

    with ZipFile(BytesIO(before_second)) as old, ZipFile(second) as current:
        assert current.read("devices/elements.db") == old.read("devices/elements.db")
