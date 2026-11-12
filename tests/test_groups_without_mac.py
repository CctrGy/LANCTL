"""P127: manual devices can join groups before their MAC is discovered."""

import os
from unittest.mock import patch

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.core.database import DeviceDatabase
from lanctl.core.group_database import GroupDatabase


def test_stable_membership_add_remove_delete_and_legacy(workspace):
    db = DeviceDatabase(workspace["database"])
    first = db.add_manual_device(alias="First")
    second = db.add_manual_device(alias="Second")
    groups = GroupDatabase(workspace["groups"], db)
    groups.create("ROOM")
    groups.add("ROOM", first.device_id)
    group = next(g for g in groups.load() if g.name == "ROOM")
    assert group.member_ids == [first.device_id] and group.members == []
    assert "ROOM" in db.resolve(first.device_id).groups
    assert "ROOM" not in db.resolve(second.device_id).groups
    groups.edit_device_fields(second.device_id, [("group", "ROOM")])
    groups.remove("ROOM", first.device_id)
    assert next(g for g in groups.load() if g.name == "ROOM").member_ids == [second.device_id]
    groups.delete_device(second.device_id)
    assert next(g for g in groups.load() if g.name == "ROOM").member_ids == []
    known = db.add_manual_device(mac="02:00:00:00:00:01", alias="Known")
    groups.add("ROOM", known.device_id)
    group = next(g for g in groups.load() if g.name == "ROOM")
    assert group.members == [known.mac] and group.member_ids == []


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_gui_checkbox_and_create_group_persist_without_mac(workspace, tmp_path):
    from test_physical_placement_gui import open_page
    from test_project_sync import projects

    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.core.config import load_config
    from lanctl.core.projects.save_policy import save_active_project
    from lanctl.core.projects.workspace import prepare_project_workspace

    project, _ = projects(workspace, tmp_path)
    cfg = load_config()
    db = DeviceDatabase(cfg["database"])
    device = db.add_manual_device(alias="Manual without MAC")
    other = db.add_manual_device(alias="Untouched")
    groups = GroupDatabase(cfg["groups"], db)
    groups.create("ROOM")
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        api = DesktopApi()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, api, "index.html")
        page.wait_for_function("state.devices?.length >= 2")
        page.evaluate("(id)=>showDeviceDetails(id)", device.device_id)
        page.locator("#tab-groups").click()
        checkbox = page.locator("#sheet-memberships label").filter(has_text="ROOM").locator("input")
        assert checkbox.is_enabled()
        checkbox.check()
        page.wait_for_function(
            "state.devices.find(d=>d.alias==='Manual without MAC').groups.includes('ROOM')"
        )
        page.locator("#sheet-new-group-name").fill("NEW")
        page.locator("#sheet-create-group").click()
        page.wait_for_function(
            "state.devices.find(d=>d.alias==='Manual without MAC').groups.includes('NEW')"
        )
        assert db.resolve(other.device_id).groups == []
        assert save_active_project(force=True).saved
        reopened = prepare_project_workspace(project, root=tmp_path / "reopened")
        stored = DeviceDatabase(reopened.database)
        assert {"ROOM", "NEW"} <= set(stored.resolve(device.device_id).groups)
        reopened_groups = GroupDatabase(reopened.groups, stored)
        assert (
            device.device_id
            in next(g for g in reopened_groups.load() if g.name == "ROOM").member_ids
        )
        browser.close()
