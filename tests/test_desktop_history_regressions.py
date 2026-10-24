"""P79: inventory history must not poison scan/save responses."""

from unittest.mock import patch

import pytest
from test_desktop_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.apps.ip.domain.discovery import DiscoveryResult
from lanctl.apps.ip.domain.models import Device
from lanctl.core import config
from lanctl.core.database import DeviceDatabase
from lanctl.core.output import AVAILABLE_COLUMNS, render_records
from lanctl.core.projects.workspace import prepare_project_workspace


@pytest.mark.parametrize("field,value", [("idf", "PC-001"), ("ip", "192.0.2.11")])
def test_edit_scan_save_undo_redo(workspace, tmp_path, field, value):
    first, _ = projects(workspace, tmp_path)
    database = DeviceDatabase(config.load_config()["database"])
    original = Device(ip="192.0.2.10", mac="02:00:00:00:00:10")
    database.save_devices([original])
    instance = api()
    result = instance.update_device(original.device_id, {field: value})
    assert result["ok"], result
    assert result["editHistory"]["canUndo"]

    scan_module = "lanctl.apps.ip.interfaces.cli.commands.list"
    discovered = database.resolve(original.device_id)
    with (
        patch(
            scan_module + ".local_ipv4",
            return_value=__import__("ipaddress").IPv4Address("192.0.2.1"),
        ),
        patch(
            scan_module + ".resolve_network",
            return_value=__import__("ipaddress").IPv4Network("192.0.2.0/24"),
        ),
        patch(
            scan_module + ".RealDiscoveryProvider.discover",
            return_value=DiscoveryResult((discovered,), "real", "test"),
        ),
        patch(scan_module + ".LanScanner.is_confirmed", return_value=True),
        patch(scan_module + ".LanScanner.discovery_for", return_value="ICMP"),
        patch(scan_module + ".LanScanner.response_time_for", return_value=1.0),
    ):
        scanned = instance.scan_network("fast")
    assert scanned["ok"], scanned
    assert any(row["id"] == original.device_id for row in scanned["devices"])
    assert instance.save_project()["ok"]
    fresh = prepare_project_workspace(first, root=tmp_path / "reopened")
    assert getattr(DeviceDatabase(str(fresh.database)).resolve(original.device_id), field) == value
    undone = instance.undo_edit()
    assert undone["ok"], undone
    assert getattr(database.resolve(original.device_id), field) == getattr(original, field)
    redone = instance.redo_edit()
    assert redone["ok"], redone
    assert getattr(database.resolve(original.device_id), field) == value


@pytest.mark.parametrize("color", [False, True])
@pytest.mark.parametrize("width", [12, 300])
def test_all_selectable_columns_render_for_inactive_devices(color, width):
    rendered = render_records(
        [Device(ip="192.0.2.10", idf="PC-001")],
        "table",
        columns=list(AVAILABLE_COLUMNS),
        active_rows=[False],
        color=color,
        max_width=width,
    )
    assert "idf" in rendered
