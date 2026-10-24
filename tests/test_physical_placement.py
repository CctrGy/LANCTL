"""Placement invariants across LANRACK/LANWIRE, persistence and old formats."""

from copy import deepcopy

import pytest

from lanctl.apps.rack.service import RackService
from lanctl.apps.wire.gui_service import WireGuiService, revision
from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.core.physical_placement import location_status, with_location


@pytest.fixture
def physical(tmp_path):
    path = tmp_path / "physical.db"
    wire = WireGuiService(path)
    rack = RackService(str(path))
    cabinet = wire.create({"prefix": "RK", "kind": "rack", "units": 12})["id"]
    panel = wire.create({"prefix": "PN", "kind": "panel", "rack": cabinet, "unit": 8})["id"]
    outlet = wire.create({"prefix": "PT", "kind": "outlet", "rack": cabinet, "in_rack": False})[
        "id"
    ]
    camera = wire.create({"prefix": "CM", "kind": "pc.1port"})["id"]
    cable = wire.create({"prefix": "WL", "kind": "wire.copper"})["id"]
    wire.connect(
        cable,
        revision(wire.database.get(cable)),
        [{"device": panel, "port": "P1"}, {"device": outlet, "port": "WALL"}],
    )
    return wire, rack, cabinet, panel, outlet, camera, cable


def edit(service, identifier, **values):
    return service.edit_element(
        service.snapshot()["organizationRevision"], "update", identifier, values
    )


def test_classification_relocation_preserves_ids_ports_and_links(physical):
    wire, rack, cabinet, panel, outlet, camera, cable = physical
    before = deepcopy(wire.database.all())
    assert {r["id"]: r["placement"]["kind"] for r in rack.elements()}[outlet] == "environment"
    assert (
        next(r for r in rack.elements() if r["id"] == camera)["placement"]["kind"] == "independent"
    )
    edit(rack, panel, rack=cabinet, in_rack=True, unit=2, heightU=3)
    edit(rack, camera, rack=cabinet, in_rack=False, unit=0)
    assert wire.database.get(cable)["data"] == next(r["data"] for r in before if r["id"] == cable)
    assert wire.database.get(panel)["data"]["ports"] == next(
        r["data"]["ports"] for r in before if r["id"] == panel
    )
    reloaded = RackService(str(wire.database.path)).get(cabinet)
    assert next(o for o in reloaded["occupants"] if o["id"] == panel)["span"] == 3
    assert next(o for o in reloaded["occupants"] if o["id"] == outlet)["unit"] == 0
    assert {r["id"] for r in wire.database.all()} == {r["id"] for r in before}


@pytest.mark.parametrize("height", [0, -1, 1.5, True, "2", 53])
def test_invalid_heights_atomic(physical, height):
    wire, rack, _, panel, *_ = physical
    original = wire.database.path.read_bytes()
    with pytest.raises(ValueError):
        edit(rack, panel, heightU=height)
    assert wire.database.path.read_bytes() == original


def test_multi_u_collision_bounds_and_stale_window(physical):
    wire, rack, cabinet, panel, outlet, *_ = physical
    edit(rack, panel, heightU=3)
    stale = rack.snapshot()["organizationRevision"]
    original = wire.database.path.read_bytes()
    for unit in (7, 8, 9, 10, 12, 0, -1, 1.2, True):
        with pytest.raises(ValueError):
            edit(rack, outlet, rack=cabinet, in_rack=True, unit=unit, heightU=2)
        assert wire.database.path.read_bytes() == original
    choices = rack.destinations(outlet, 2)["destinations"]
    assert {c["unit"] for c in choices} == {1, 2, 3, 4, 5, 6, 11}
    edit(rack, outlet, rack=cabinet, in_rack=True, unit=1, heightU=2)
    with pytest.raises(ValueError, match="inventario cambió"):
        rack.edit_element(stale, "update", panel, {"unit": 3})
    with pytest.raises(ValueError, match="fuera"):
        rack.set_dimensions(
            rack.snapshot()["organizationRevision"], cabinet, {"units": 9, "widthInches": 19}
        )


def test_tray_hosts_multiple_devices_without_double_occupancy(physical):
    wire, rack, cabinet, _, outlet, camera, cable = physical
    tray = rack.edit_element(
        rack.snapshot()["organizationRevision"],
        "create",
        "",
        {"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": 1, "heightU": 2},
    )["id"]
    before_cable = wire.database.get(cable)
    for identifier in (outlet, camera):
        edit(rack, identifier, tray=tray)
        data = wire.database.get(identifier)["data"]
        assert data["location"] == {
            "schemaVersion": 1,
            "tray": tray,
            "rack": None,
            "in_rack": False,
            "unit": 0,
        }
    edit(rack, tray, unit=4, heightU=3)
    snapshot = RackService(str(wire.database.path)).get(cabinet)
    assert next(o for o in snapshot["occupants"] if o["id"] == outlet)["placement"]["unit"] == 4
    assert next(o for o in snapshot["occupants"] if o["id"] == outlet)["unit"] == 0
    assert wire.database.get(cable) == before_cable
    with pytest.raises(ValueError, match="Reubica"):
        wire.database.delete(tray)
    with pytest.raises(ValueError):
        edit(rack, tray, tray=tray)
    with pytest.raises(ValueError, match="Reubica"):
        edit(rack, tray, rack=None, unit=0, in_rack=False)
    edit(rack, outlet, tray=None, rack=cabinet, in_rack=False, unit=0)
    edit(rack, camera, tray=None, rack=None, in_rack=False, unit=0)
    wire.database.delete(tray)
    assert wire.database.get(outlet) and wire.database.get(camera)
    assert wire.database.get(cable) == before_cable


def test_legacy_ambiguous_location_is_not_silently_environment(tmp_path):
    db = IDFDatabaseManager(tmp_path / "legacy.db")
    db.add("RK-01", {"type": "rack", "units": 12})
    db.add("SW-01", {"type": "device.switch", "location": {"rack": "RK-01"}})
    db.add("SW-02", {"type": "device.switch", "location": {"rack": "RK-01", "unit": 2}})
    before = db.path.read_bytes()
    rack = RackService(str(db.path))
    elements = {r["id"]: r for r in rack.elements()}
    assert elements["SW-01"]["placement"]["needsReview"]
    assert elements["SW-02"]["placement"]["kind"] == "inside"
    assert db.path.read_bytes() == before
    edit(rack, "SW-01", rack="RK-01", in_rack=False, unit=0)
    assert db.get("SW-01")["data"]["location"]["schemaVersion"] == 1


def test_storage_boundary_validates_other_interfaces(physical):
    wire, _, cabinet, panel, outlet, *_ = physical
    data = wire.database.get(outlet)["data"]
    for bad in (
        with_location(data, rack=cabinet, in_rack=False, unit=3),
        with_location(data, rack=cabinet, in_rack=True, unit=8),
        with_location(data, rack="RK-99", in_rack=True, unit=1),
        with_location(data, tray=panel),
        with_location(data, in_rack=True, unit=0),
    ):
        original = wire.database.path.read_bytes()
        with pytest.raises(ValueError):
            wire.database.update(outlet, bad)
        assert wire.database.path.read_bytes() == original
    assert location_status(data, wire.database.all())["kind"] == "environment"


def test_cli_and_tui_use_same_placement_and_span(physical, capsys):
    from lanctl.apps.rack.cli import main
    from lanctl.apps.wire.tui.detail import rack_occupant, selectable_ports
    from lanctl.apps.wire.tui.editor import editable_fields, set_field

    wire, rack, cabinet, panel, outlet, *_ = physical
    assert (
        main(
            [
                "--database",
                str(wire.database.path),
                "element",
                panel,
                "--placement",
                "inside",
                "--rack",
                cabinet,
                "--unit",
                "2",
                "--height-u",
                "3",
            ]
        )
        == 0
    )
    records = wire.database.all()
    cabinet_record = wire.database.get(cabinet)
    assert len(selectable_ports(cabinet_record)) == 12
    assert rack_occupant(cabinet_record, records, 4)["id"] == panel
    record = wire.database.get(outlet)
    field = next(f for f in editable_fields(record) if f.label == "unit")
    set_field(record["data"], field, "6")
    wire.database.update(outlet, record["data"])
    assert next(r for r in rack.elements() if r["id"] == outlet)["placement"]["kind"] == "inside"
    assert (
        main(
            [
                "--database",
                str(wire.database.path),
                "add-element",
                "--kind",
                "tray",
                "--prefix",
                "TR",
            ]
        )
        == 0
    )
    assert any(r["data"]["type"] == "tray" for r in wire.database.all())


def test_legacy_tray_conversion_and_moved_layout_no_duplicate(physical):
    from lanctl.apps.wire.tui.detail import rack_occupant

    wire, rack, cabinet, panel, *_ = physical
    record = wire.database.get(cabinet)
    record["data"]["layout"] = [
        {"unit": 3, "height": 2, "kind": "tray", "label_lines": ["Bandeja", ""]},
        {"unit": 8, "height": 1, "kind": "panel", "idf": panel},
    ]
    wire.database.update(cabinet, record["data"])
    with pytest.raises(ValueError, match="heredado"):
        edit(rack, panel, unit=3)
    result = rack.edit_element(
        rack.snapshot()["organizationRevision"], "import-tray", cabinet, {"unit": 3}
    )
    tray = wire.database.get(result["id"])
    assert tray["data"]["rackAppearance"]["units"] == 2
    assert tray["data"]["location"]["unit"] == 3
    edit(rack, result["id"], unit=5)
    edit(rack, panel, unit=1)
    records = wire.database.all()
    cabinet_record = wire.database.get(cabinet)
    assert rack_occupant(cabinet_record, records, 8) is None
    assert rack_occupant(cabinet_record, records, 1)["id"] == panel
    assert not any(i.get("kind") == "tray" for i in cabinet_record["data"]["layout"])


def test_concurrent_creations_cannot_share_units(physical):
    from concurrent.futures import ThreadPoolExecutor

    wire, _, cabinet, *_ = physical

    def create():
        try:
            return wire.create(
                {"prefix": "SV", "kind": "server.2ports", "rack": cabinet, "unit": 1, "heightU": 2}
            )
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: create(), range(2)))
    assert sum(r is not None for r in results) == 1


def test_populated_tray_blocks_rack_deletion_and_bad_input_is_atomic(physical):
    wire, rack, cabinet, _, outlet, *_ = physical
    tray = wire.create({"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": 2})["id"]
    edit(rack, outlet, tray=tray)
    before = wire.database.path.read_bytes()
    with pytest.raises(ValueError, match="bandejas"):
        wire.database.delete(cabinet)
    assert wire.database.path.read_bytes() == before
    for values in (
        {"unit": False},
        {"unit": 1.5},
        {"rack": cabinet, "in_rack": False, "unit": 2},
        {"tray": tray, "rack": cabinet},
    ):
        with pytest.raises(ValueError):
            edit(rack, outlet, **values)
        assert wire.database.path.read_bytes() == before


def test_legacy_out_of_bounds_is_visible_for_review(physical):
    import json

    wire, rack, _, panel, *_ = physical
    document = json.loads(wire.database.path.read_text(encoding="utf-8"))
    document["records"][panel]["data"]["location"] = {"rack": "RK-00", "unit": 99}
    wire.database.path.write_text(json.dumps(document), encoding="utf-8")
    before = wire.database.path.read_bytes()
    assert next(r for r in rack.elements() if r["id"] == panel)["placement"]["needsReview"]
    assert wire.database.path.read_bytes() == before


def test_deletion_does_not_invalidate_unrelated_revisions(physical):
    from unittest.mock import patch

    wire, _, _, _, _, camera, cable = physical
    before = wire.database.get(cable)
    with patch.object(wire.database, "_timestamp", return_value="2099-01-01T00:00:00+00:00"):
        wire.database.delete(camera)
    assert wire.database.get(cable) == before


def test_environment_requires_existing_rack_even_in_empty_inventory(tmp_path):
    wire = WireGuiService(tmp_path / "empty.db")
    with pytest.raises(ValueError, match="rack"):
        wire.create({"kind": "outlet", "prefix": "PT", "rack": "RK-99", "in_rack": False})
    assert wire.database.all() == []


def test_moving_tray_between_racks_moves_effective_children_and_preserves_cable(physical):
    wire, rack, cabinet, _, outlet, _, cable = physical
    other = wire.create({"kind": "rack", "prefix": "RK", "units": 4})["id"]
    tray = wire.create({"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": 2, "heightU": 2})[
        "id"
    ]
    edit(rack, outlet, tray=tray)
    before = wire.database.get(cable)
    edit(rack, tray, rack=other, in_rack=True, unit=3)
    assert all(o["id"] not in {tray, outlet} for o in rack.get(cabinet)["occupants"])
    assert (
        next(o for o in rack.get(other)["occupants"] if o["id"] == outlet)["placement"]["rack"]
        == other
    )
    assert wire.database.get(cable) == before
    original = wire.database.path.read_bytes()
    with pytest.raises(ValueError):
        edit(rack, tray, unit=4)
    assert wire.database.path.read_bytes() == original
