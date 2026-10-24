"""Native creation is atomic and bound to the displayed project/launcher."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.apps.wire.gui_service import WireGuiService
from lanctl.core.projects.workspace import activate_project_workspace


@pytest.mark.parametrize(
    "failure",
    [
        "occupied",
        "duplicate",
        "missing-port",
        "missing-device",
        "medium",
        "too-many",
        "malformed",
        "not-cable",
    ],
)
def test_bad_cable_creation_leaves_inventory_unchanged(workspace, failure):
    wire = api("lanwire")
    identifier = wire.wire_create({"kind": "switch.5ports", "prefix": "SW"})["id"]
    end = {"device": identifier, "port": "X1"}
    if failure == "occupied":
        existing = wire.wire_create({"kind": "wire.copper", "prefix": "WL", "endpoints": [end]})
        assert existing["ok"], existing
    ends, kind = [end], "wire.copper"
    if failure == "duplicate":
        ends *= 2
    elif failure == "missing-port":
        ends = [{**end, "port": "MISSING"}]
    elif failure == "missing-device":
        ends = [{**end, "device": "SW-99"}]
    elif failure == "medium":
        kind = "wire.fiber"
    elif failure == "too-many":
        ends *= 3
    elif failure == "malformed":
        ends = [None]
    elif failure == "not-cable":
        kind = "pc.1port"
    path = Path(wire._service.database.path)
    before = path.read_bytes()
    rejected = wire.wire_create({"kind": kind, "prefix": "WL", "endpoints": ends})
    assert not rejected["ok"], rejected
    assert rejected["errorId"] and rejected["errorDetails"]
    assert path.read_bytes() == before


def test_competing_creations_cannot_claim_same_port(workspace):
    wire = api("lanwire")
    identifier = wire.wire_create({"kind": "switch.5ports", "prefix": "SW"})["id"]
    path = wire._service.database.path

    def create(_):
        try:
            return WireGuiService(path).create(
                {
                    "kind": "wire.copper",
                    "prefix": "WL",
                    "endpoints": [{"device": identifier, "port": "X1"}],
                }
            )
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(create, range(2)))
    assert sum(result is not None for result in results) == 1
    assert len(wire._service.database.all()) == 2


def test_cpd_launcher_permissions_revision_and_project_guard(workspace, tmp_path):
    _, second = projects(workspace, tmp_path)
    wire = api("lanwire")
    snapshot = wire.bootstrap()
    result = wire.project_call(
        snapshot["projectContext"],
        "wire_organization",
        [snapshot["organizationRevision"], "create", {"name": "CPD"}],
    )
    assert result["ok"], result
    assert api("lanrack").bootstrap()["cpds"] == wire.bootstrap()["cpds"]
    assert not wire.wire_organization(
        snapshot["organizationRevision"], "create", {"name": "Stale"}
    )["ok"]
    for name in ("lanrack", "lanmon", "lanaccess"):
        assert not api(name).wire_organization(
            wire.bootstrap()["organizationRevision"], "create", {"name": "Forbidden"}
        )["ok"]
    assert not wire.rack_organization(
        wire.bootstrap()["organizationRevision"], "create", {"name": "Forbidden"}
    )["ok"]
    assert wire.save_project()["ok"]
    activate_project_workspace(second)
    for method, args in (
        (
            "wire_organization",
            [wire.bootstrap()["organizationRevision"], "create", {"name": "Wrong"}],
        ),
        ("wire_create", [{"kind": "wire.copper", "prefix": "WL"}]),
    ):
        result = wire.project_call(snapshot["projectContext"], method, args)
        assert not result["ok"] and "proyecto cambió" in result["error"]
    assert wire.bootstrap()["records"] == [] and wire.bootstrap()["cpds"] == []
