"""Accessory fronts are selectable and persist without inventing network ports."""

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace

from lanctl.apps.rack.skins import profiles
from lanctl.apps.wire.idf.database import IDFDatabaseManager


@pytest.mark.parametrize("kind", ["cable-comb", "organizer", "ventilation", "blank"])
def test_accessory_front_creation_and_saved_choice_preserve_inventory(workspace, kind):
    rack = api("lanrack")
    cabinet = rack.rack_element(
        rack.bootstrap()["organizationRevision"],
        "create",
        "",
        {"kind": "rack", "prefix": "RK", "units": 12},
    )["id"]
    created = rack.rack_element(
        rack.bootstrap()["organizationRevision"],
        "create",
        "",
        {"kind": kind, "prefix": "AC", "rack": cabinet, "unit": 2, "heightU": 2},
    )
    assert created["ok"], created
    identifier = created["id"]
    database = rack._service.database
    before = database.get(identifier)
    assert before["data"]["rackAppearance"]["kind"] == kind
    assert before["data"]["ports"] == {}
    profile = next(p for p in profiles() if p["id"] == f"{kind}-2")
    assert rack.rack_appearance(rack.bootstrap()["organizationRevision"], identifier, profile)["ok"]
    reloaded = IDFDatabaseManager(database.path).get(identifier)
    assert reloaded["data"] == before["data"]
    # Explicit older/custom fronts stay valid and are not silently replaced.
    old = {**profile, "kind": "blank"}
    assert rack.rack_appearance(rack.bootstrap()["organizationRevision"], identifier, old)["ok"]
    final = database.get(identifier)
    assert final["data"]["rackAppearance"]["kind"] == "blank"
    for key in ("location", "ports", "type"):
        assert final["data"][key] == before["data"][key]
    assert final["id"] == identifier
