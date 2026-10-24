"""P81: resize real rack views without changing inventory or losing controls."""

import os
from copy import deepcopy
from pathlib import Path

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


@pytest.mark.parametrize("units", [4, 18, 52])
def test_rack_automatic_scale_preserves_units_and_editing(workspace, units):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create(
        {
            "kind": "rack",
            "prefix": "RK",
            "units": units,
            "name": f"Rack de {units} U",
            "description": "Descripción extensa " * 50,
        }
    )["id"]
    lower = wire.wire_create(
        {"kind": "server.2ports", "prefix": "SV", "rack": cabinet, "unit": 1, "heightU": 2}
    )["id"]
    upper = wire.wire_create(
        {
            "kind": "switch.24ports",
            "prefix": "SW",
            "rack": cabinet,
            "unit": units,
            "name": "Switch con nombre largo para comprobar el recorte legible",
        }
    )["id"]
    before = deepcopy(wire.bootstrap()["records"])
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        # Old preferences keep the selected representation, but never force scale.
        page = open_page(
            browser,
            rack,
            init_script="""localStorage.setItem('lanrack.skins.preferences',
            JSON.stringify({schemaVersion:1, visible:false, unitHeight:84}));""",
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        assert page.locator(".rack-face").count() == 0
        assert page.locator(".rack-elevation > button").count() == units
        page.get_by_role("button", name="Ver frentes de equipos", exact=True).click()
        assert page.locator(".rack-skin-empty").count() == units - 3
        assert page.locator("input[type=range]").count() == 0
        assert page.get_by_role("button", name="Abrir LANWIRE", exact=True).count() == 0
        for name in ("Actualizar", "Nuevo CPD", "Nuevo rack", "Nuevo elemento"):
            assert page.get_by_role("button", name=name, exact=True).is_visible()
        sizes = []
        for width, height in [(1440, 1000), (850, 700), (800, 600), (1920, 1080)]:
            page.set_viewport_size({"width": width, "height": height})
            # Wait for two paint frames, including ResizeObserver delivery.
            page.evaluate(
                "() => new Promise(resolve => requestAnimationFrame("
                "() => requestAnimationFrame(resolve)))"
            )
            measure = page.evaluate(
                """() => {
                  const canvas = document.querySelector('#canvas');
                  const elevation = document.querySelector('.rack-elevation');
                  const rows = [...elevation.querySelectorAll(':scope > button')];
                  const rects = rows.map(r => r.getBoundingClientRect());
                  const header = document.querySelector('.rack-detail-header');
                  return {
                    unit: parseFloat(getComputedStyle(elevation)
                                      .getPropertyValue('--rack-unit-height')),
                    noHorizontalOverflow: canvas.scrollWidth <= canvas.clientWidth + 1
                      && document.documentElement.scrollWidth <= innerWidth,
                    noOverlaps: rects.every((r, i) => !i || r.top >= rects[i-1].bottom),
                    headerHeight: header.offsetHeight,
                    footerBottom: document.querySelector('footer').getBoundingClientRect().bottom,
                    labelSize: parseFloat(getComputedStyle(
                      document.querySelector('.rack-skin-caption')).fontSize),
                  };
                }"""
            )
            sizes.append(measure["unit"])
            assert 30 <= measure["unit"] <= 84
            assert measure["noHorizontalOverflow"], (width, height, measure)
            assert measure["noOverlaps"]
            assert measure["headerHeight"] < 125
            assert measure["footerBottom"] <= height + 1
            assert measure["labelSize"] >= 12
            empty = page.locator(".rack-skin-empty").first.bounding_box()
            server = page.locator(f'[data-rack-occupant="{lower}"]').bounding_box()
            assert abs(server["height"] - (2 * empty["height"] + 3)) < 1
            # Both extremities remain reachable and open the real shared editor.
            for identifier in (upper, lower):
                page.locator(f'[data-rack-occupant="{identifier}"]').click()
                assert page.locator("#detail").is_visible()
                page.locator("#cancel").click()
                page.wait_for_function("!document.querySelector('#detail').open")
                back = page.locator("#rack-back").bounding_box()
                canvas = page.locator("#canvas").bounding_box()
                assert back["y"] >= canvas["y"] - 1
                assert back["y"] + back["height"] <= canvas["y"] + canvas["height"]
        if units < 52:
            assert max(sizes) > min(sizes)  # Resize really changes the visual scale.
        page.locator("#rack-skins-toggle").click()
        assert page.locator(".rack-elevation > button").count() == units
        page.locator("#rack-skins-toggle").click()
        page.locator("#rack-back").click()
        assert page.locator(f'[data-rack-open="{cabinet}"]').is_visible()
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        assert page.locator(".rack-face").count() == 2
        assert wire.bootstrap()["records"] == before
        assert not errors, errors
        browser.close()


def test_rack_resize_retains_open_form_and_unsaved_values(workspace):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 18})["id"]
    device = wire.wire_create(
        {"kind": "router.gateway", "prefix": "RT", "rack": cabinet, "unit": 1}
    )["id"]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, rack)
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        page.locator(f'[data-rack-occupant="{device}"]').click()
        name = page.locator("[name=name]")
        name.fill("Editado tras redimensionar")
        page.set_viewport_size({"width": 800, "height": 600})
        assert name.input_value() == "Editado tras redimensionar"
        assert name.evaluate("el => el === document.activeElement")
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        assert wire._service.database.get(device)["data"]["name"] == "Editado tras redimensionar"
        page.screenshot(path=str(Path(".tool-reports/p81-rack-small.png").resolve()))
        browser.close()
