"""An imported LANIP IDF can be completed without replacing its identity."""

from copy import deepcopy

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace

from lanctl.apps.wire.gui_service import revision
from lanctl.core.database import DeviceDatabase


@pytest.mark.parametrize("launcher", ["lanwire", "lanrack"])
def test_complete_existing_idf_preserves_logical_identity_and_placement(workspace, launcher):
    client = api(launcher)
    service = client._service
    database = service.database
    rack = database.add("RK-01", {"type": "rack", "units": 24})
    original = database.add(
        "SW-01",
        {
            "type": "element",
            "name": "Switch L3",
            "alias": "SW",
            "ip": "192.168.1.253",
            "ports": {},
            "location": {
                "rack": rack["id"],
                "schemaVersion": 1,
                "in_rack": True,
                "unit": 13,
                "tray": None,
            },
        },
    )
    logical = DeviceDatabase(workspace["database"])
    device = logical.add_manual_device(name="Switch L3", ip="192.168.1.253", idf="SW-01")
    before = logical.path.read_bytes()
    if launcher == "lanrack":
        result = client.rack_element(
            client.bootstrap()["organizationRevision"],
            "update",
            "SW-01",
            {"switchProfile": "switch.24rj45.4sfp"},
        )
    else:
        result = client.wire_update(
            "SW-01", revision(original), {"switchProfile": "switch.24rj45.4sfp"}
        )
    assert result["ok"], result
    updated = database.get("SW-01")
    assert updated["id"] == original["id"] and updated["created_at"] == original["created_at"]
    assert updated["data"]["type"] == "device.switch"
    assert len(updated["data"]["ports"]) == 28
    for key in ("name", "alias", "ip", "location"):
        assert updated["data"][key] == original["data"][key]
    assert logical.path.read_bytes() == before
    assert logical.resolve(device.device_id).idf == "SW-01"
    assert len(database.all()) == 2


def test_profile_completion_rejects_invalid_stale_and_already_configured_devices(workspace):
    client = api("lanwire")
    database = client._service.database
    record = database.add("SW-01", {"type": "element", "ports": {}})
    original = database.path.read_bytes()
    for profile in ("router.gateway", {}, None, "switch.nonexistent"):
        result = client.wire_update("SW-01", revision(record), {"switchProfile": profile})
        assert not result["ok"]
        assert database.path.read_bytes() == original
    assert client.wire_update("SW-01", revision(record), {"switchProfile": "switch.24ports"})["ok"]
    after = database.path.read_bytes()
    assert not client.wire_update("SW-01", revision(record), {"switchProfile": "switch.48ports"})[
        "ok"
    ]
    current = deepcopy(database.get("SW-01"))
    assert not client.wire_update("SW-01", revision(current), {"switchProfile": "switch.48ports"})[
        "ok"
    ]
    assert database.path.read_bytes() == after


@pytest.mark.parametrize("profile", ["switch.24ports", "switch.24rj45.4sfp"])
def test_profile_preserves_existing_height_for_legacy_and_mixed_profiles(workspace, profile):
    client = api("lanwire")
    database = client._service.database
    original = database.add(
        "SW-01",
        {
            "type": "element",
            "ports": {},
            "rackAppearance": {
                "schemaVersion": 1,
                "kind": "auto",
                "rj45": 0,
                "sfp": 0,
                "rackmount": True,
                "units": 2,
            },
        },
    )
    result = client.wire_update("SW-01", revision(original), {"switchProfile": profile})
    assert result["ok"], result
    assert database.get("SW-01")["data"]["rackAppearance"]["units"] == 2
