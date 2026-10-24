"""P85-P87: actual topology interactions, labels, outlet geometry and ports."""

import os
from pathlib import Path

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page, save_form

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_direct_edit_labels_and_compact_outlet_connections(workspace):
    wire = api("lanwire")
    ids = {}
    for name, kind, prefix in (
        ("Switch", "switch.5ports", "SW"),
        ("OTG", "router.otg", "OT"),
        ("Toma A", "outlet", "PX"),
        ("Toma B", "outlet", "PX"),
        ("Armario", "rack", "RK"),
    ):
        ids[name] = wire.wire_create({"kind": kind, "prefix": prefix, "name": name})["id"]
    for index, name in enumerate(("Toma A", "Toma B"), 1):
        result = wire.wire_create(
            {
                "kind": "wire.copper",
                "prefix": "WL",
                "name": f"Enlace {index}",
                "endpoints": [
                    {"device": ids["Switch"], "port": f"X{index}"},
                    {"device": ids[name], "port": "WALL"},
                ],
            }
        )
        assert result["ok"], result
    path = Path(wire._service.database.path)
    before = path.read_bytes()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, wire)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.locator("#wire-board").wait_for()
        # Data opens directly; no intermediate action menu or implicit mutation.
        for name in ("Switch", "OTG", "Toma A", "Toma B"):
            page.locator(f'[data-node="{ids[name]}"] strong').dblclick()
            assert page.locator("[name=name]").input_value() == name
            assert "Acciones" not in page.locator("#detail-title").inner_text()
            page.locator("#cancel").click()
        assert path.read_bytes() == before
        page.locator(f'[data-node="{ids["OTG"]}"] strong').dblclick()
        page.locator("[name=name]").fill("OTG editado")
        save_form(page)
        assert wire._service.database.get(ids["OTG"])["data"]["name"] == "OTG editado"
        page.locator(f'[data-node="{ids["OTG"]}"] strong').click(button="right")
        assert page.get_by_role("button", name="Centrar", exact=True).is_visible()
        page.locator("#cancel").click()
        # Only cable names change; positions, selection, zoom and device IDs stay.
        before = path.read_bytes()
        geometry = page.evaluate("JSON.stringify({positions:wirePositions,camera,selected})")
        paths = page.locator("#wire-lines path").count()
        assert page.locator(".physical-cable-label").count() == 2
        page.get_by_role("button", name="Ocultar nombres de cables", exact=True).click()
        assert page.locator(".physical-cable-label").count() == 0
        assert page.locator("#wire-lines path").count() == paths
        assert page.locator(f'[data-node="{ids["Toma A"]}"] small').is_visible()
        assert (
            page.evaluate("JSON.stringify({positions:wirePositions,camera,selected})") == geometry
        )
        page.evaluate("refresh()")
        page.get_by_role("button", name="Mostrar nombres de cables", exact=True).wait_for()
        assert page.locator(".physical-cable-label").count() == 0
        page.get_by_role("button", name="Mostrar nombres de cables", exact=True).click()
        assert page.locator(".physical-cable-label").count() == 2
        assert path.read_bytes() == before
        # Generic two-port outlet is about a quarter of its old 240x119 area.
        for name in ("Toma A", "Toma B"):
            node = page.locator(f'[data-node="{ids[name]}"]')
            dimensions = node.evaluate(
                "e=>({w:e.offsetWidth,h:e.offsetHeight,overflow:e.scrollHeight>e.clientHeight})"
            )
            assert 0.20 <= dimensions["w"] * dimensions["h"] / (240 * 119) <= 0.32
            assert not dimensions["overflow"]
            assert node.locator("[data-port]").count() == 2
            for zoom in (0.7, 1.2):
                page.evaluate("z=>{camera.z=z;wirePaint()}", zoom)
                anchor = page.evaluate("id=>wireAnchor({device:id,port:'WALL'})", ids[name])
                position = page.evaluate("id=>wirePositions[id]", ids[name])
                assert position["x"] <= anchor["x"] <= position["x"] + dimensions["w"]
                assert position["y"] <= anchor["y"] <= position["y"] + dimensions["h"]
        page.locator('[data-nav="fit"]').click()
        page.screenshot(path=str(Path(".tool-reports/p85-p87-topology.png").resolve()))
        # Racks also open data directly; explicit navigation remains available.
        page.get_by_role("button", name="Vista general de racks", exact=True).click()
        page.locator(f'[data-node="{ids["Armario"]}"] strong').dblclick()
        assert page.locator("[name=name]").input_value() == "Armario"
        page.locator("#cancel").click()
        page.locator(f'[data-node="{ids["Armario"]}"] strong').click(button="right")
        page.get_by_role("button", name="Ver interior del rack", exact=True).click()
        assert page.evaluate("physicalLevel") == "inside"
        assert not errors, errors
        browser.close()
