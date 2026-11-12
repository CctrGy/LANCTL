"""A fixed 1U five-device host shares tray persistence and storage guards."""

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.core.physical_placement import location_status
from lanctl.core.projects.workspace import activate_project_workspace


def change(service, identifier, **values):
    return service.rack_element(
        service.bootstrap()["organizationRevision"], "update", identifier, values
    )


def populate(rack):
    cabinet = rack.rack_element(
        rack.bootstrap()["organizationRevision"],
        "create",
        "",
        {"kind": "rack", "prefix": "RK", "units": 18},
    )["id"]
    result = rack.rack_element(
        rack.bootstrap()["organizationRevision"],
        "create",
        "",
        {"kind": "raspberry-pi-panel", "prefix": "RP", "rack": cabinet, "unit": 4},
    )
    assert result["ok"], result
    panel = result["id"]
    db = rack._service.database
    children = []
    for i in range(6):
        r = db.add(
            f"PI-{i + 1:02}", {"type": "element", "name": f"Raspberry Pi {i + 1}", "ports": {}}
        )
        children.append(r["id"])
    return cabinet, panel, children


def test_five_device_limit_relocation_removal_and_reopen(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    rack = api("lanrack")
    cabinet, panel, children = populate(rack)
    db = rack._service.database
    for child in children[:5]:
        assert change(rack, child, tray=panel)["ok"]
    before = db.path.read_bytes()
    sixth = change(rack, children[5], tray=panel)
    assert not sixth["ok"] and sixth["errorId"]
    assert db.path.read_bytes() == before
    # Editing one of the five does not count the same occupant twice.
    assert change(rack, children[0], tray=panel)["ok"]
    assert change(rack, panel, unit=8)["ok"]
    assert location_status(db.get(children[0])["data"], db.all())["unit"] == 8
    assert len(rack._service.get(cabinet)["occupants"]) == 6
    assert change(rack, children[0], tray=None, rack=None, in_rack=False, unit=0)["ok"]
    assert change(rack, children[5], tray=panel)["ok"]
    assert rack.save_project()["ok"]
    activate_project_workspace(first, root=tmp_path / "reopened", refresh=True)
    rows = {r["id"]: r for r in rack.bootstrap()["elements"]}
    assert rows[panel]["data"]["rackAppearance"]["units"] == 1
    assert sum((r["data"].get("location") or {}).get("tray") == panel for r in rows.values()) == 5
    assert rows[children[5]]["placement"]["unit"] == 8
    assert list(rows[children[5]]["data"]["ports"]) == ["LAN1"]
    assert not rows[children[0]]["data"]["location"]["tray"]


def test_fixed_height_capacity_and_nested_containers_enforced_at_storage(workspace):
    rack = api("lanrack")
    cabinet, panel, children = populate(rack)
    db = rack._service.database
    before = db.path.read_bytes()
    for height in (0, 2, 3):
        assert not change(rack, panel, heightU=height)["ok"]
        assert db.path.read_bytes() == before
    visual = {**db.get(panel)["data"]["rackAppearance"], "units": 2}
    assert not rack.rack_appearance(rack.bootstrap()["organizationRevision"], panel, visual)["ok"]
    assert db.path.read_bytes() == before
    tray = db.add("TR-01", {"type": "tray", "ports": {}})
    assert not change(rack, tray["id"], tray=panel)["ok"]
    for child in children[:5]:
        assert change(rack, child, tray=panel)["ok"]
    before = db.path.read_bytes()
    candidate = {
        **db.get(children[5])["data"],
        "location": {"schemaVersion": 1, "tray": panel, "rack": None, "in_rack": False, "unit": 0},
    }
    with pytest.raises(ValueError):
        db.update(children[5], candidate)
    assert db.path.read_bytes() == before
    with pytest.raises(ValueError):
        db.delete(panel)
    with pytest.raises(ValueError):
        db.delete(cabinet)
    assert db.path.read_bytes() == before


def test_unmounted_panel_rejects_height_two_even_via_appearance(workspace):
    rack = api("lanrack")
    p = rack.rack_element(
        rack.bootstrap()["organizationRevision"],
        "create",
        "",
        {"kind": "raspberry-pi-panel", "prefix": "RP"},
    )["id"]
    db = IDFDatabaseManager(rack._service.database.path)
    assert db.get(p)["data"]["ports"] == {}
    before = db.path.read_bytes()
    visual = {**db.get(p)["data"]["rackAppearance"], "units": 2}
    assert not rack.rack_appearance(rack.bootstrap()["organizationRevision"], p, visual)["ok"]
    assert db.path.read_bytes() == before
    visual = {**db.get(p)["data"]["rackAppearance"], "rackmount": False}
    assert not rack.rack_appearance(rack.bootstrap()["organizationRevision"], p, visual)["ok"]
    assert db.path.read_bytes() == before
    assert p not in {r["id"] for r in api("lanwire").bootstrap()["records"]}


def test_ordinary_trays_keep_their_existing_unlimited_capacity(workspace):
    rack = api("lanrack")
    cabinet, _, children = populate(rack)
    tray = rack.rack_element(
        rack.bootstrap()["organizationRevision"],
        "create",
        "",
        {"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": 10},
    )["id"]
    for child in children:
        assert change(rack, child, tray=tray)["ok"]
    assert (
        sum(
            (r["data"].get("location") or {}).get("tray") == tray
            for r in rack._service.database.all()
        )
        == 6
    )


def test_each_pi_has_one_real_rj45_and_can_connect_to_lanwire(workspace):
    rack, wire = api("lanrack"), api("lanwire")
    _, panel, children = populate(rack)
    assert change(rack, children[0], tray=panel)["ok"]
    db = rack._service.database
    board = db.get(children[0])
    assert board["data"]["type"] == "device.raspberry-pi"
    assert list(board["data"]["ports"]) == ["LAN1"]
    assert board["data"]["ports"]["LAN1"]["kind"] == "connection.rj45"
    created = rack.rack_element(
        rack.bootstrap()["organizationRevision"],
        "create",
        "",
        {"kind": "raspberry-pi", "prefix": "PI", "tray": panel},
    )
    assert created["ok"], created
    assert len(db.get(created["id"])["data"]["ports"]) == 1
    peer = wire.wire_create({"kind": "switch.24ports", "prefix": "SW"})["id"]
    cable = wire.wire_create(
        {
            "kind": "wire.copper",
            "prefix": "WL",
            "endpoints": [{"device": children[0], "port": "LAN1"}, {"device": peer, "port": "X1"}],
        }
    )
    assert cable["ok"], cable
    assert children[0] in {r["id"] for r in wire.bootstrap()["records"]}
    assert db.get(panel)["data"]["ports"] == {}
    before = db.path.read_bytes()
    bad = {**db.get(children[0])["data"], "ports": {}}
    with pytest.raises(ValueError):
        db.update(children[0], bad)
    bad["ports"] = {"LAN1": {"kind": "connection.fiber"}}
    with pytest.raises(ValueError):
        db.update(children[0], bad)
    bad["ports"] = {"LAN1": {"kind": "connection.rj45"}, "LAN2": {"kind": "connection.rj45"}}
    with pytest.raises(ValueError):
        db.update(children[0], bad)
    assert db.path.read_bytes() == before


def test_existing_single_port_and_connections_preserved_multipoort_rejected(workspace):
    from lanctl.apps.wire.gui_service import revision

    rack, wire = api("lanrack"), api("lanwire")
    _, panel, _ = populate(rack)
    device = wire.wire_create({"kind": "pc.1port", "prefix": "PC"})["id"]
    db = rack._service.database
    row = db.get(device)
    assert wire.wire_port(device, revision(row), "LAN1", "ETH0", 1)["ok"]
    cable = wire.wire_create(
        {"kind": "wire.copper", "prefix": "WL", "endpoints": [{"device": device, "port": "ETH0"}]}
    )
    assert cable["ok"]
    ports = db.get(device)["data"]["ports"]
    links = db.get(cable["id"])
    assert change(rack, device, tray=panel)["ok"]
    assert db.get(device)["data"]["ports"] == ports
    assert db.get(cable["id"]) == links
    incompatible = wire.wire_create({"kind": "pc.2ports", "prefix": "PC"})["id"]
    before = db.path.read_bytes()
    assert not change(rack, incompatible, tray=panel)["ok"]
    assert db.path.read_bytes() == before
