import json

import pytest

from lanctl.apps.rack.service import RackService
from lanctl.apps.wire.gui_service import WireGuiService
from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.core.rack_dimensions import dimension_status


@pytest.mark.parametrize("units", [4, 52])
@pytest.mark.parametrize("width", [10, 19, 21, 23])
def test_dimensions_roundtrip_through_shared_database(tmp_path, units, width):
    path = tmp_path / "idf.db"
    wire = WireGuiService(path)
    identifier = wire.create(
        {"kind": "rack", "prefix": "RK", "units": units, "widthInches": width}
    )["id"]
    rack = RackService(str(path)).get(identifier)
    assert (rack["units"], rack["widthInches"]) == (units, width)
    assert not rack["dimensions"]["needsReview"]
    assert wire.database.get(identifier)["data"]["rackDimensions"] == {
        "schemaVersion": 1,
        "widthInches": width,
    }


@pytest.mark.parametrize("units", [3, 53, 4.5, True, "42", None])
def test_invalid_height_rejected_without_coercion(tmp_path, units):
    wire = WireGuiService(tmp_path / "idf.db")
    with pytest.raises(ValueError):
        wire.create({"kind": "rack", "prefix": "RK", "units": units})
    with pytest.raises(ValueError):
        wire.database.add("RK-01", {"type": "rack", "units": units})
    assert wire.database.all() == []


@pytest.mark.parametrize("width", [9, 20, 24, 19.0, True, "19"])
def test_invalid_width_refused(tmp_path, width):
    wire = WireGuiService(tmp_path / "idf.db")
    with pytest.raises(ValueError):
        wire.create({"kind": "rack", "prefix": "RK", "units": 42, "widthInches": width})


def test_shrink_rejected_in_shared_database_and_stale_editor(tmp_path):
    path = tmp_path / "idf.db"
    service = RackService(str(path))
    service.database.add("RK-01", {"type": "rack", "units": 42})
    service.database.add(
        "SW-01", {"type": "device.switch", "location": {"rack": "RK-01", "unit": 40}}
    )
    expected = service.snapshot()["organizationRevision"]
    before = path.read_bytes()
    with pytest.raises(ValueError, match="fuera"):
        service.set_dimensions(expected, "RK-01", {"units": 39, "widthInches": 19})
    assert path.read_bytes() == before
    service.set_dimensions(expected, "RK-01", {"units": 52, "widthInches": 23})
    with pytest.raises(ValueError, match="cambió"):
        service.set_dimensions(expected, "RK-01", {"units": 52, "widthInches": 19})
    data = service.database.get("RK-01")["data"]
    data["units"] = 4
    with pytest.raises(ValueError, match="fuera"):
        service.database.update("RK-01", data)
    assert service.database.get("SW-01")["data"]["location"]["unit"] == 40


def test_legacy_out_of_range_and_unknown_width_preserved_until_explicit_edit(tmp_path):
    path = tmp_path / "idf.db"
    database = IDFDatabaseManager(path)
    database.add("RK-01", {"type": "rack", "units": 42})
    document = json.loads(path.read_text(encoding="utf-8"))
    document["records"]["RK-01"]["data"] = {"type": "rack", "size_units": 60, "name": "legacy"}
    path.write_text(json.dumps(document), encoding="utf-8")
    before = path.read_bytes()
    service = RackService(str(path))
    rack = service.get("RK-01")
    assert rack["units"] == 60 and rack["widthInches"] is None
    assert rack["dimensions"]["needsReview"]
    assert path.read_bytes() == before
    service.set_dimensions(
        service.snapshot()["organizationRevision"], "RK-01", {"units": 52, "widthInches": 21}
    )
    reopened = IDFDatabaseManager(path).get("RK-01")["data"]
    assert reopened["units"] == reopened["size_units"] == 52
    assert not dimension_status(reopened)["needsReview"]


def test_in_memory_rack_model_uses_same_dimension_contract():
    from lanctl.apps.wire.models.rack import NetworkRack

    assert NetworkRack("test", 52, width_inches=23).width_inches == 23
    with pytest.raises(ValueError):
        NetworkRack("test", 3)
    with pytest.raises(ValueError):
        NetworkRack("test", 4, width_inches=20)
