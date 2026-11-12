"""Provider fiber boundary: one real port, LANWIRE symbol and VLF persistence."""

import os
from pathlib import Path

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page, save_form
from test_project_sync import projects

from lanctl.apps.wire.topology import FIBER, build_new_idf_data, build_ports
from lanctl.core.inventory_visibility import visible_in
from lanctl.core.projects.workspace import activate_project_workspace


def test_provider_profile_and_visibility():
    data = build_new_idf_data("external.fiber-entry")
    assert data["type"] == "external.fiber-entry"
    assert set(data["ports"]) == {"FIBER"}
    assert data["ports"]["FIBER"]["kind"] == FIBER
    assert data["ports"]["FIBER"]["connectorGender"] == "female"
    for launcher in ("lanwire", "lanrack", "lanip", "lanaccess", "lanmon"):
        assert visible_in(data, launcher, logical_ip="192.0.2.2") == (launcher == "lanwire")


def test_provider_connection_visibility_atomic_errors_and_reopen(workspace, tmp_path):
    first, second = projects(workspace, tmp_path)
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    entry = wire.wire_create(
        {
            "kind": "external.fiber-entry",
            "prefix": "FE",
            "name": "Entrada de fibra",
        }
    )["id"]
    otg = wire.wire_create({"kind": "router.otg", "prefix": "OT", "name": "OTG"})["id"]
    before = wire._service.database.path.read_bytes()
    assert not wire.wire_create(
        {"kind": "wire.copper", "prefix": "WL", "endpoints": [{"device": entry, "port": "FIBER"}]}
    )["ok"]
    assert wire._service.database.path.read_bytes() == before
    for position in (
        {"rack": cabinet, "in_rack": True, "unit": 1},
        {"rack": cabinet, "in_rack": False, "unit": 0},
    ):
        assert not wire.wire_create({"kind": "external.fiber-entry", "prefix": "FE", **position})[
            "ok"
        ]
        assert wire._service.database.path.read_bytes() == before
    endpoints = [{"device": entry, "port": "FIBER"}, {"device": otg, "port": "FIBER"}]
    cable = wire.wire_create(
        {
            "kind": "wire.fiber",
            "prefix": "FB",
            "name": "Entrada de compañia",
            "endpoints": endpoints,
        }
    )["id"]
    before = wire._service.database.path.read_bytes()
    assert not wire.wire_create({"kind": "wire.fiber", "prefix": "FB", "endpoints": endpoints})[
        "ok"
    ]
    assert wire._service.database.path.read_bytes() == before
    assert entry in {r["id"] for r in wire.bootstrap()["records"]}
    assert entry not in {r["id"] for r in rack.bootstrap()["elements"]}
    assert entry not in {r["id"] for r in rack.bootstrap()["records"][0]["occupants"]}
    assert wire.save_project()["ok"]
    activate_project_workspace(second)
    activate_project_workspace(first, root=tmp_path / "reopened")
    records = {r["id"]: r for r in wire.bootstrap()["records"]}
    assert records[cable]["data"]["endpoints"] == endpoints
    assert records[entry]["data"]["ports"]["FIBER"]["kind"] == FIBER
    assert entry not in {r["id"] for r in rack.bootstrap()["elements"]}


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
@pytest.mark.parametrize("language", ["es", "en"])
def test_provider_creation_circle_and_fiber_connection_gui(
    workspace, tmp_path, monkeypatch, language
):
    from lanctl.core import config
    from lanctl.shared import i18n

    projects(workspace, tmp_path)
    manager = i18n.LanguageManager(tmp_path / "languages")
    manager.initialize()
    manager.install(Path(__file__).resolve().parents[1] / "bundled/languages/spanish.lang")
    monkeypatch.setattr(i18n, "_MANAGER", manager)
    cfg = config.load_config()
    cfg["language"] = language
    config.save_config(cfg)
    wire, rack = api("lanwire"), api("lanrack")
    otg = wire.wire_create({"kind": "router.otg", "prefix": "OT", "name": "OTG"})["id"]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = open_page(browser, wire)
        failures = []
        page.on("pageerror", lambda error: failures.append(str(error)))
        page.evaluate("wireNew()")
        page.locator('[name="kind"]').select_option("external.fiber-entry")
        page.locator('[name="name"]').fill("Entrada de fibra")
        save_form(page)
        entry = next(
            r["id"]
            for r in wire.bootstrap()["records"]
            if r["data"].get("type") == "external.fiber-entry"
        )
        page.evaluate("wireNew('wire.fiber')")
        page.locator('[name="name"]').fill("Entrada de compañia")
        page.locator('[name="endpointA"]').select_option(label="Entrada de fibra · FIBER")
        page.locator('[name="endpointB"]').select_option(label="OTG · FIBER")
        save_form(page)
        cable = next(r for r in wire.bootstrap()["records"] if r["data"].get("type") == "wire")
        assert cable["data"]["endpoints"] == [
            {"device": entry, "port": "FIBER"},
            {"device": otg, "port": "FIBER"},
        ]
        page.evaluate(
            "view='topology';physicalLevel='inside';physicalRack='';physicalCpd='';render();wireFit()"
        )
        node = page.locator(f'[data-node="{entry}"]')
        assert page.evaluate(
            """id => {
            const p=wirePositions[id], size=physicalSize(wireGraph.nodes.find(n=>n.id===id));
            return physicalRegions.filter(r=>!r.external).every(r=>
              p.x+size.w<=r.x || r.x+r.w<=p.x || p.y+size.h<=r.y || r.y+r.h<=p.y);
        }""",
            entry,
        )
        assert node.locator("svg circle").count() == 2
        assert node.locator("[data-port]").count() == 1
        assert node.locator('circle[data-port="FIBER"]').is_visible()
        assert page.locator(f'[data-cable="{cable["id"]}"]').count() > 0
        # An old saved position inside a green area is moved back outside it.
        assert page.evaluate(
            """({entry,otg})=>{
            wirePositions[entry]={...wirePositions[otg]};wirePaint();
            const p=wirePositions[entry];
            return physicalRegions.filter(r=>!r.external).every(r=>p.x+160<=r.x);
        }""",
            {"entry": entry, "otg": otg},
        )
        output = Path(os.environ.get("LANCTL_PROVIDER_REVIEW_DIR", str(tmp_path)))
        output.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(output / f"provider-fiber-{language}.png"))
        page.evaluate("physicalSwitchLevel('outside')")
        assert page.locator(f'[data-node="{entry}"]').is_visible()
        assert page.evaluate("id=>physicalRegions.find(r=>r.id==='@external:'+id)?.external", entry)
        assert page.locator(f'[data-node="{entry}"] [data-port="FIBER"]').is_visible()
        rack_page = open_page(browser, rack)
        rack_page.evaluate("wireNew()")
        assert rack_page.locator('[name="kind"] option[value="external.fiber-entry"]').count() == 0
        assert not failures, failures
        browser.close()


def test_provider_otg_gateway_switch_chain(workspace):
    wire = api("lanwire")
    entry = wire.wire_create({"kind": "external.fiber-entry", "prefix": "FE"})["id"]
    otg = wire.wire_create({"kind": "router.otg", "prefix": "OT"})["id"]
    gateway = wire.wire_create({"kind": "router.gateway", "prefix": "RT", "name": "GATEWAY"})["id"]
    data = wire._service.database.get(gateway)["data"]
    data["ports"] = build_ports(2, "WLAN,LAN1")
    wire._service.database.update(gateway, data)
    switch = wire.wire_create({"kind": "switch.26rj45.2sfp", "prefix": "SW"})["id"]
    for kind, prefix, endpoints in [
        (
            "wire.fiber",
            "FB",
            [{"device": entry, "port": "FIBER"}, {"device": otg, "port": "FIBER"}],
        ),
        (
            "wire.copper",
            "WL",
            [{"device": otg, "port": "WLAN"}, {"device": gateway, "port": "WLAN"}],
        ),
        (
            "wire.copper",
            "WL",
            [{"device": gateway, "port": "LAN1"}, {"device": switch, "port": "X25"}],
        ),
    ]:
        result = wire.wire_create({"kind": kind, "prefix": prefix, "endpoints": endpoints})
        assert result["ok"], result
        assert wire._service.database.get(result["id"])["data"]["endpoints"] == endpoints
