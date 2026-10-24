"""Frentes de rack persistentes sin alterar el inventario de puertos."""

import os
from copy import deepcopy
from pathlib import Path

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page

from lanctl.apps.rack.skins import profiles

pytest_plugins = ["test_launcher_gui"]


def setup_rack():
    wire, rack = api("lanwire"), api("lanrack")
    rack_id = wire.wire_create(
        {"kind": "rack", "prefix": "RK", "units": 18, "name": "Armario principal"}
    )["id"]
    devices = []
    for kind, prefix, name, unit in [
        ("switch.24ports", "SW", "Switch Rack", 13),
        ("panel", "PN", "Panel de conexiones", 10),
        ("server.2ports", "SV", "Servidor", 5),
    ]:
        identifier = wire.wire_create({"kind": kind, "prefix": prefix, "name": name})["id"]
        row = next(r for r in wire.bootstrap()["records"] if r["id"] == identifier)
        assert wire.wire_update(identifier, row["revision"], {"rack": rack_id, "unit": unit})["ok"]
        devices.append(identifier)
    ups = wire._service.database.create(
        "UP", data={"type": "device.ups", "name": "SAI", "location": {"rack": rack_id, "unit": 1}}
    )["id"]
    return wire, rack, rack_id, [*devices, ups]


def save(rack, identifier, profile):
    return rack.rack_appearance(rack.bootstrap()["organizationRevision"], identifier, profile)


def test_skin_catalog_and_shared_storage_integrity(workspace):
    wire, rack, rack_id, devices = setup_rack()
    catalog = {p["id"]: p for p in profiles()}
    assert {
        "switch-12-0",
        "switch-24-0",
        "switch-48-0",
        "switch-48-2",
        "switch-50-2",
        "switch-48-4",
        "server-2",
        "ups-3",
        "desktop-8",
    } <= catalog.keys()
    before = deepcopy(wire.bootstrap()["records"])
    assert save(rack, devices[0], catalog["switch-48-4"])["ok"]
    assert save(rack, devices[2], catalog["server-2"])["ok"]
    assert save(rack, devices[3], catalog["ups-3"])["ok"]
    after = wire.bootstrap()["records"]
    for a, b in zip(before, after, strict=True):
        assert a["id"] == b["id"]
        data = deepcopy(b["data"])
        data.pop("rackAppearance", None)
        assert a["data"] == data
    snapshot = rack.bootstrap()["records"][0]
    assert snapshot["id"] == rack_id
    assert next(r for r in snapshot["occupants"] if r["id"] == devices[2])["span"] == 2
    stale = rack.bootstrap()["organizationRevision"]
    assert save(rack, devices[0], catalog["switch-24-0"])["ok"]
    assert not rack.rack_appearance(stale, devices[0], catalog["desktop-8"])["ok"]
    assert not wire.rack_appearance(
        wire.bootstrap()["organizationRevision"], devices[0], catalog["desktop-8"]
    )["ok"]


def test_skin_height_conflicts_and_wire_moves(workspace):
    wire, rack, rack_id, devices = setup_rack()
    profile = next(p for p in profiles() if p["id"] == "server-2")
    assert save(rack, devices[2], profile)["ok"]
    before = deepcopy(wire.bootstrap()["records"])
    assert not save(rack, devices[2], {**profile, "units": 8})["ok"]  # Panel en U10.
    assert not save(rack, devices[0], {**profile, "units": 8})["ok"]  # Fuera del rack.
    assert not save(rack, devices[0], {**profile, "rj45": True})["ok"]
    assert wire.bootstrap()["records"] == before
    row = next(r for r in before if r["id"] == devices[0])
    assert not wire.wire_update(row["id"], row["revision"], {"rack": rack_id, "unit": 6})["ok"]
    row = next(r for r in before if r["id"] == rack_id)
    assert not wire.wire_update(row["id"], row["revision"], {"units": 5})["ok"]


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_rack_skins_visual_editor_and_real_save(workspace):
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    wire, rack, rack_id, devices = setup_rack()
    catalog = {p["id"]: p for p in profiles()}
    assert save(rack, devices[2], catalog["server-2"])["ok"]
    assert save(rack, devices[3], catalog["ups-3"])["ok"]
    root = Path(__file__).resolve().parents[1]
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.expose_function("rpc", lambda method, args: getattr(rack, method)(*args))
        page.goto((root / "gui/launcher.html").as_uri())
        page.evaluate(
            "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
        )
        page.locator(f'[data-rack-open="{rack_id}"]').click()
        front = page.locator(f'[data-rack-occupant="{devices[0]}"]')
        assert front.locator('[data-connector="rj45"]').count() == 24
        assert page.locator(".rack-face.skin-server").count() == 1
        assert page.locator(".rack-face.skin-ups").count() == 1
        assert page.locator(".rack-skin-empty").count() == 11
        empty = page.locator(".rack-skin-empty").first.bounding_box()
        assert abs(front.bounding_box()["height"] - empty["height"]) < 1
        server = page.locator(f'[data-rack-occupant="{devices[2]}"]').bounding_box()
        assert abs(server["height"] - (2 * empty["height"] + 3)) < 1
        front.click()
        page.get_by_role("button", name="Personalizar frente", exact=True).click()
        for profile in catalog.values():
            page.locator("[name=preset]").select_option(profile["id"])
            assert page.locator(".rack-skin-preview svg").count() == 1
        page.locator("[name=preset]").select_option("switch-48-4")
        assert page.locator('.rack-skin-preview [data-connector="rj45"]').count() == 48
        assert page.locator('.rack-skin-preview [data-connector="sfp"]').count() == 4
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        assert (
            page.locator(f'[data-rack-occupant="{devices[0]}"] [data-connector="sfp"]').count() == 4
        )
        record = next(r for r in wire.bootstrap()["records"] if r["id"] == devices[0])
        assert len(record["data"]["ports"]) == 24
        page.screenshot(path=str(root / "tmp/lanrack-skins.png"))
        page.locator("#rack-skins-toggle").click()
        assert page.locator(".rack-face").count() == 0
        page.locator("#rack-skins-toggle").click()
        assert page.locator(".rack-face").count() == 4
        assert page.locator(".rack-skin-size input").count() == 0
        assert (
            page.evaluate(
                "JSON.parse(localStorage.getItem('lanrack.skins.preferences')).schemaVersion"
            )
            == 1
        )
        page.set_viewport_size({"width": 850, "height": 700})
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        assert page.locator("footer").bounding_box()["y"] < 700
        assert not errors, errors
        browser.close()


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
@pytest.mark.parametrize("units", [9, 12, 52])
def test_large_equipment_front_preserves_height_and_connections(workspace, units):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": max(18, units)})["id"]
    device = wire.wire_create(
        {"kind": "server.2ports", "prefix": "SV", "rack": cabinet, "unit": 1, "heightU": units}
    )["id"]
    peer = wire.wire_create({"kind": "pc.1port", "prefix": "PC"})["id"]
    cable = wire.wire_create({"kind": "wire.copper", "prefix": "WL"})["id"]
    records = {r["id"]: r for r in wire.bootstrap()["records"]}
    assert wire.wire_connect(
        cable,
        records[cable]["revision"],
        [
            {"device": device, "port": next(iter(records[device]["data"]["ports"]))},
            {"device": peer, "port": next(iter(records[peer]["data"]["ports"]))},
        ],
    )["ok"]
    before = deepcopy(wire.bootstrap()["records"])
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, rack)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.locator(f'[data-rack-open="{cabinet}"]').click()

        def edit_front():
            page.locator(f'[data-rack-occupant="{device}"]').click()
            page.get_by_role("button", name="Personalizar frente", exact=True).click()

        edit_front()
        height = page.locator("[name=units]")
        assert height.input_value() == str(units)
        assert height.evaluate("e => e.checkValidity()")
        assert page.locator(".rack-skin-preview svg").get_attribute("viewBox") == (
            f"0 0 1200 {88 * units}"
        )
        for invalid in ("0", "53", "1.5"):
            height.fill(invalid)
            page.locator("#submit").click()
            assert not height.evaluate("e => e.checkValidity()")
            assert page.locator("#detail").is_visible()
            assert wire.bootstrap()["records"] == before
        if units < 18:
            # Within the editor's range, but outside this rack: Core still rejects it.
            height.fill("19")
            page.locator("#submit").click()
            page.wait_for_function("!!document.querySelector('#detail-error').textContent")
            assert page.locator("#detail").is_visible()
            assert wire.bootstrap()["records"] == before
            page.locator('[data-error="close"]').click()
        height.fill(str(units))
        page.locator("[name=kind]").select_option("server")
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        for old, new in zip(before, wire.bootstrap()["records"], strict=True):
            assert old["id"] == new["id"]
            old_data, new_data = deepcopy(old["data"]), deepcopy(new["data"])
            if new["id"] == device:
                assert new_data["rackAppearance"]["units"] == units
                assert new_data["rackAppearance"]["kind"] == "server"
                old_data.pop("rackAppearance")
                new_data.pop("rackAppearance")
            assert old_data == new_data
        edit_front()
        assert height.input_value() == str(units)
        assert height.evaluate("e => e.checkValidity()")
        page.locator("#cancel").click()
        assert not errors, errors
        browser.close()
