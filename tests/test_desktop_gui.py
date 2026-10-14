from threading import Thread
from unittest.mock import Mock, patch

from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi, DesktopProgress

MODULE = "lanctl.apps.ip.interfaces.gui.desktop"


def api():
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        return DesktopApi()


def test_progress_is_nonblocking_and_cancellable():
    progress = DesktopProgress()
    progress.begin(10)
    progress.advance(3)
    assert progress.snapshot() == {"total": 10, "current": 3, "found": 0}
    progress.stop.set()
    assert progress.cancelled()


def test_rpc_does_not_autosave_on_reads():
    instance = api()
    with patch("lanctl.core.projects.save_policy.save_active_project") as save:
        assert instance._respond(lambda: {"value": 1}) == {"ok": True, "value": 1}
    save.assert_not_called()


def test_editor_rejects_stale_revision(tmp_path):
    from lanctl.apps.ip.domain.models import Device
    from lanctl.core.database import DeviceDatabase
    from lanctl.core.group_database import GroupDatabase

    instance = api()
    database = DeviceDatabase(str(tmp_path / "devices.json"))
    original = Device.from_dict({"IP": "192.0.2.1", "MAC": "02:00:00:00:00:01", "NAME": "before"})
    revision = instance._edit_revision(original)
    modified = original.copy()
    modified.name = "another session"
    database.save_devices([modified])
    groups = GroupDatabase(str(tmp_path / "groups.json"), database)
    with (
        patch.object(instance, "_database", return_value=database),
        patch.object(instance, "_groups", return_value=groups),
    ):
        result = instance.update_device(original.mac, {"name": "stale change"}, revision)
    assert not result["ok"]
    assert "otra sesión" in result["error"]
    assert database.resolve(original.mac).name == "another session"


def test_operation_does_not_queue_behind_scan():
    instance = api()
    results = []
    with instance._lock:
        thread = Thread(target=lambda: results.append(instance.project_state()))
        thread.start()
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert results[0]["ok"] is False


def test_failed_save_does_not_close_window():
    instance = api()
    instance._window = Mock()
    with (
        patch(f"{MODULE}.load_config", return_value={}),
        patch(f"{MODULE}.workspace_is_dirty", return_value=True),
        patch.object(instance, "save_project", return_value={"ok": False, "error": "disk full"}),
    ):
        result = instance.request_close("save")
    assert result["ok"] is False
    instance._window.destroy.assert_not_called()


def test_cancel_close_preserves_window():
    instance = api()
    instance._window = Mock()
    assert instance.request_close()["closed"] is False
    instance._window.destroy.assert_not_called()


def test_project_switch_passes_explicit_discard_and_clears_presence(tmp_path):
    instance = api()
    instance._activity["old"] = True
    with (
        patch(f"{MODULE}.load_config", return_value={}),
        patch(f"{MODULE}.workspace_is_dirty", return_value=True),
        patch(f"{MODULE}.resolve_project_path", return_value=tmp_path / "new.vlf"),
        patch(f"{MODULE}.inspect_project"),
        patch(f"{MODULE}.activate_project_workspace") as activate,
        patch.object(instance, "_inventory_payload", return_value={}),
        patch.object(instance, "_projects_payload", return_value={}),
        patch("lanctl.core.plugins.manager.get_plugin_manager"),
    ):
        assert instance.use_project("new", True)["ok"]
    activate.assert_called_once_with(tmp_path / "new.vlf", discard_changes=True)
    assert not instance._activity


def test_create_project_has_empty_inventory_and_no_credentials(tmp_path):
    instance = api()
    with (
        patch(f"{MODULE}.load_config", return_value={"credentials": "private"}),
        patch(f"{MODULE}.workspace_is_dirty", return_value=False),
        patch(f"{MODULE}.resolve_project_path", return_value=tmp_path / "new.vlf"),
        patch(
            f"{MODULE}.create_project", return_value={"path": str(tmp_path / "new.vlf")}
        ) as create,
        patch(f"{MODULE}.activate_project_workspace"),
        patch.object(instance, "_inventory_payload", return_value={}),
        patch.object(instance, "_projects_payload", return_value={}),
    ):
        assert instance.create_project("new")["ok"]
    options = create.call_args.kwargs
    assert options["initialize_reserved"] is False
    assert options["config"]["credentials"] != "private"
    assert options["config"]["databaseLog"] is None


def test_settings_are_allowlisted_without_exposing_credentials():
    instance = api()
    with patch(f"{MODULE}.load_config", return_value={"credentials": "secret"}):
        payload = instance.get_settings()
    assert "secret" not in str(payload)
