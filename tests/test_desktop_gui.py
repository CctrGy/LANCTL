from threading import Thread
from unittest.mock import Mock, patch

from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi, DesktopProgress

MODULE = "lanctl.apps.ip.interfaces.gui.desktop"


def test_long_device_description_roundtrips_through_edit_and_reload(tmp_path):
    from lanctl.apps.ip.domain.models import Device
    from lanctl.core.database import DeviceDatabase
    from lanctl.core.group_database import GroupDatabase

    instance = api()
    database = DeviceDatabase(str(tmp_path / "devices.json"))
    device = Device(ip="192.0.2.10", mac="02:00:00:00:00:10", description="a" * 10000)
    database.save_devices([device])
    groups = GroupDatabase(str(tmp_path / "groups.json"), database)
    with (
        patch.object(instance, "_database", return_value=database),
        patch.object(instance, "_groups", return_value=groups),
        patch("lanctl.core.projects.save_policy.save_active_project"),
    ):
        result = instance.update_device(device.device_id, {"description": "Detalle\n" * 2000})
    assert result["ok"], result
    assert database.resolve(device.device_id).description == ("Detalle\n" * 2000).strip()


def test_open_lanctl_gui_does_not_use_shell():
    with (
        patch("lanctl.apps.suite.processes.launcher_command", return_value=["lanctl", "--gui"]),
        patch("lanctl.apps.suite.processes.process_options", return_value={}),
        patch(f"{MODULE}.subprocess.Popen") as process,
    ):
        assert api().open_suite()["ok"]
    assert process.call_args.args[0] == ["lanctl", "--gui"]
    assert "shell" not in process.call_args.kwargs


def test_create_group_with_description_and_invalid_description_is_atomic(tmp_path):
    from lanctl.core.database import DeviceDatabase
    from lanctl.core.group_database import GroupDatabase

    instance = api()
    devices = DeviceDatabase(str(tmp_path / "devices.json"))
    groups = GroupDatabase(str(tmp_path / "groups.json"), devices)
    with (
        patch.object(instance, "_database", return_value=devices),
        patch.object(instance, "_groups", return_value=groups),
        patch("lanctl.core.projects.save_policy.save_active_project"),
    ):
        result = instance.create_group("oficina", "Equipos de oficina")
        assert result["ok"], result
        assert any(group["name"] == "OFICINA" for group in result["groupCatalog"])
        assert (
            next(group for group in groups.load() if group.name == "OFICINA").description
            == "Equipos de oficina"
        )
        assert not instance.create_group("otro", "x" * 43)["ok"]
        assert "OTRO" not in [group.name for group in groups.load()]


def test_lanip_cli_button_opens_lanip_not_suite():
    with patch("lanctl.apps.suite.processes.open_system_cli") as launch:
        assert api().open_cli()["ok"]
    launch.assert_called_once_with("lanip")


def test_settings_include_scan_retention_projects_and_logging_options():
    fields = api().get_settings()["fields"]
    by_key = {field["key"]: field for field in fields}
    assert {
        "scanOrder",
        "dhcpRange",
        "disconnectedRetention",
        "serviceIdentification",
        "projectSaveIntervalMinutes",
        "logRetentionDays",
    } <= by_key.keys()
    assert by_key["serviceIdentification"]["choices"] == ["on", "off"]


def test_complete_device_record_is_passive_and_redacts_secrets(tmp_path):
    from lanctl.apps.ip.domain.models import Device
    from lanctl.core.database import DeviceDatabase

    instance = api()
    database = DeviceDatabase(str(tmp_path / "devices.json"))
    device = Device.from_dict(
        {
            "IP": "192.0.2.1",
            "MAC": "02:00:00:00:00:01",
            "NAME": "Router",
            "previousIPs": ["192.0.2.20"],
            "discoveryMethods": ["ARP"],
            "credentials": {"http": "private-reference"},
            "protocolOptions": {"http": {"password": "private-password", "port": 8080}},
        }
    )
    database.save_devices([device])
    with (
        patch.object(instance, "_database", return_value=database),
        patch.object(instance, "_diagnose") as diagnose,
    ):
        result = instance.device_record(device.device_id)
    assert result["ok"]
    assert result["record"]["previousIPs"] == ["192.0.2.20"]
    assert "private-reference" not in str(result)
    assert "private-password" not in str(result)
    diagnose.assert_not_called()


def test_web_service_opens_directly_without_a_console(tmp_path):
    from lanctl.apps.ip.domain.models import Device
    from lanctl.core.database import DeviceDatabase

    instance = api()
    database = DeviceDatabase(str(tmp_path / "devices.json"))
    device = Device.from_dict(
        {"IP": "192.0.2.1", "MAC": "02:00:00:00:00:01", "protocols": ["https"]}
    )
    database.save_devices([device])
    with (
        patch.object(instance, "_database", return_value=database),
        patch(
            f"{MODULE}.load_config",
            return_value={"database": str(database.path), "credentials": "store"},
        ),
        patch(
            "lanctl.apps.ip.interfaces.cli.commands.open.run_open", return_value=0
        ) as open_target,
        patch(f"{MODULE}.subprocess.Popen") as process,
    ):
        assert instance.open_service(device.device_id, "https", 8443)["ok"]
    assert open_target.call_args.args[0].port == 8443
    assert open_target.call_args.args[0].protocol == "https"
    process.assert_not_called()


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
