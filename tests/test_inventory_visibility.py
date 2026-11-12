"""P136 view filtering preserves shared inventory, IDs and relationships."""

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace

from lanctl.core.inventory_visibility import validate_management, visible_in


@pytest.mark.parametrize(
    "kind",
    ["tray", "device.tray", "rack.cable-comb", "rack.organizer", "rack.ventilation", "rack.pdu"],
)
def test_rack_only(kind):
    for launcher in ("lanwire", "lanip", "lanaccess", "lanmon"):
        assert not visible_in({"type": kind}, launcher)
    assert visible_in({"type": kind}, "lanrack")


def test_management_is_explicit_and_ip_changes_visibility():
    unknown = {"type": "device.switch"}
    assert visible_in(unknown, "lanip")
    unmanaged = {**unknown, "management": {"schemaVersion": 1, "managed": False}}
    assert not visible_in(unmanaged, "lanip")
    assert visible_in(unmanaged, "lanwire")
    assert visible_in(unmanaged, "lanip", logical_ip="192.0.2.2")
    assert not visible_in({"type": "rack.ups"}, "lanwire")
    assert visible_in({"type": "rack.ups", "ip": "192.0.2.3"}, "lanwire")
    assert visible_in({"type": "device.router"}, "lanip")
    with pytest.raises(ValueError):
        validate_management({"schemaVersion": 1, "managed": "false"})


def test_gui_visibility_preserves_storage_and_hosted_devices(workspace):
    from lanctl.apps.ip.interfaces.gui.main import GuiApi
    from lanctl.core.database import DeviceDatabase

    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    ids = {}
    for kind, prefix, unit in [
        ("tray", "TR", 1),
        ("pdu", "PD", 3),
        ("ups", "UP", 4),
        ("organizer", "OR", 5),
        ("ventilation", "VN", 6),
        ("cable-comb", "CM", 7),
    ]:
        result = wire.wire_create({"kind": kind, "prefix": prefix, "rack": cabinet, "unit": unit})
        assert result["ok"], result
        ids[kind] = result["id"]
    switch = wire.wire_create(
        {
            "kind": "switch.5ports",
            "prefix": "SW",
            "management": {"schemaVersion": 1, "managed": False},
        }
    )["id"]
    child = wire.wire_create({"kind": "router.gateway", "prefix": "RT", "tray": ids["tray"]})["id"]
    from lanctl.apps.wire.gui_service import revision

    cable = wire.wire_create({"kind": "wire.copper", "prefix": "WL"})["id"]
    from lanctl.apps.wire.topology import compatible_connection

    endpoints = [
        {
            "device": identifier,
            "port": next(
                name
                for name, port in wire._service.database.get(identifier)["data"]["ports"].items()
                if compatible_connection(wire._service.database.get(cable)["data"], port)[0]
            ),
        }
        for identifier in (switch, child)
    ]
    assert wire.wire_connect(cable, revision(wire._service.database.get(cable)), endpoints)["ok"]
    db = DeviceDatabase(workspace["database"])
    for identifier in [*ids.values(), switch, child]:
        db.add_manual_device(idf=identifier, alias=identifier)
    before = wire._service.database.path.read_bytes(), db.path.read_bytes()
    wire_ids = {r["id"] for r in wire.bootstrap()["records"]}
    assert not set(ids.values()) & wire_ids
    assert {switch, child, cable} <= wire_ids
    rack_ids = {r["id"] for r in rack.bootstrap()["elements"]}
    assert set(ids.values()) <= rack_ids
    logical_ids = {r["idf"] for r in GuiApi()._inventory_payload()["devices"]}
    assert not (set(ids.values()) | {switch}) & logical_ids
    assert child in logical_ids
    assert before == (wire._service.database.path.read_bytes(), db.path.read_bytes())
    record = wire._service.database.get(switch)
    assert wire.wire_update(
        switch, revision(record), {"management": {"schemaVersion": 1, "managed": True}}
    )["ok"]
    assert switch in {r["idf"] for r in GuiApi()._inventory_payload()["devices"]}
    db.edit_device(ids["ups"], "ip", "192.0.2.20")
    assert ids["ups"] in {r["id"] for r in wire.bootstrap()["records"]}
    assert ids["ups"] in {r["idf"] for r in GuiApi()._inventory_payload()["devices"]}
    from lanctl.apps.access.gui_service import AccessGuiService

    access = AccessGuiService(workspace["database"], workspace["credentials"])
    visible_ids = {r["id"] for r in access.snapshot()["devices"]}
    linked = {r.idf: r.device_id for r in db.load()}
    assert linked[child] in visible_ids
    assert not {linked[ids[kind]] for kind in ids if kind != "ups"} & visible_ids


@pytest.mark.skipif(
    __import__("os").environ.get("LANCTL_GUI_BROWSER_TESTS") != "1",
    reason="optional browser runtime",
)
def test_wire_creation_filters_and_management_edit(workspace):
    import os

    from test_physical_placement_gui import open_page

    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    tray = wire.wire_create({"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": 1})["id"]
    child = wire.wire_create({"kind": "router.gateway", "prefix": "RT", "tray": tray})["id"]
    switch = wire.wire_create({"kind": "switch.24ports", "prefix": "SW"})["id"]
    original = wire._service.database.path.read_bytes()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, wire)
        page.wait_for_function("state.records?.length > 0")
        assert page.evaluate("(id)=>state.records.some(r=>r.id===id)", tray) is False
        page.evaluate("wireNew()")
        options = page.locator("[name=kind] option").evaluate_all("(items)=>items.map(i=>i.value)")
        assert not {"tray", "organizer", "ventilation", "cable-comb", "pdu", "ups"} & set(options)
        assert wire._service.database.path.read_bytes() == original
        page.locator("#cancel").click()
        record = next(r for r in wire.bootstrap()["records"] if r["id"] == switch)
        page.evaluate("(r)=>fullDetails(r)", record)
        page.locator("[name=managed]").select_option("no")
        page.locator("#submit").click()
        page.wait_for_function(
            "!document.querySelector('#detail').open || Boolean(document.querySelector('#detail-error').textContent)"
        )
        assert not page.locator("#detail-error").inner_text()
        assert not page.locator("#detail").evaluate("d=>d.open"), page.locator(
            "#detail-form"
        ).evaluate(
            "f=>[...f.elements].filter(e=>!e.checkValidity()).map(e=>({name:e.name,message:e.validationMessage}))"
        )
        assert wire._service.database.get(switch)["data"]["management"]["managed"] is False
        assert switch in {r["id"] for r in wire.bootstrap()["records"]}
        child_record = next(r for r in wire.bootstrap()["records"] if r["id"] == child)
        assert page.evaluate("r=>physicalRegionOf(r)", child_record) == cabinet
        page.evaluate("r=>fullDetails(r)", child_record)
        page.locator('[name="name"]').fill("Hosted router preserved")
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        assert wire._service.database.get(child)["data"]["location"]["tray"] == tray
        page.goto("about:blank")
        page.close()
        page = open_page(browser, rack)
        page.wait_for_function("state.elements?.length > 0")
        assert page.evaluate("(id)=>state.elements.some(r=>r.id===id)", tray)
        browser.close()


def test_management_classification_survives_project_reopen(workspace, tmp_path):
    from test_project_sync import projects

    from lanctl.apps.wire.idf.database import IDFDatabaseManager
    from lanctl.core.projects.physical import workspace_path
    from lanctl.core.projects.save_policy import save_active_project
    from lanctl.core.projects.workspace import prepare_project_workspace

    project, _ = projects(workspace, tmp_path)
    wire = api("lanwire")
    result = wire.wire_create(
        {
            "kind": "switch.5ports",
            "prefix": "SW",
            "management": {"schemaVersion": 1, "managed": False},
        }
    )
    assert result["ok"]
    assert save_active_project(force=True).saved
    reopened = prepare_project_workspace(project, root=tmp_path / "reopened")
    record = IDFDatabaseManager(workspace_path(reopened.database)).get(result["id"])
    assert record["data"]["management"] == {"schemaVersion": 1, "managed": False}
    assert not visible_in(record["data"], "lanip")
