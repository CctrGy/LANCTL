"""P130: unit actions target occupants, create in place and assign existing IDs."""

import os

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page, save_form

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


@pytest.mark.parametrize("skins", [True, False])
def test_unit_context_actions(workspace, skins, tmp_path):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    occupant = wire.wire_create(
        {
            "kind": "server.2ports",
            "prefix": "SR",
            "name": "Original",
            "rack": cabinet,
            "unit": 2,
            "heightU": 2,
        }
    )["id"]
    existing = wire.wire_create({"kind": "pc.1port", "prefix": "PC", "name": "Independent"})["id"]
    small = [
        wire.wire_create({"kind": kind, "prefix": prefix})["id"]
        for kind, prefix in (
            ("router.gateway", "RT"),
            ("router.otg", "OT"),
            ("switch.5ports", "SW"),
        )
    ]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, rack)
        page.set_default_timeout(7000)
        page.evaluate("rackSkinsVisible = " + str(skins).lower())
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        page.locator('[data-rack-unit="2"]').click(button="right")
        menu = page.locator(".rack-unit-context")
        bounds = menu.bounding_box()
        assert bounds["x"] >= 0 and bounds["y"] >= 0
        assert bounds["x"] + bounds["width"] <= 1440
        assert bounds["y"] + bounds["height"] <= 1000
        assert not page.locator("#detail").evaluate("element => element.open")
        page.screenshot(path=str(tmp_path / "rack-context-menu.png"))
        page.keyboard.press("Escape")
        assert menu.count() == 0
        page.locator('[data-rack-unit="2"]').click(button="right")
        actions = page.locator(".rack-unit-context > button")
        assert actions.count() == 3
        assert actions.nth(2).is_disabled()
        actions.nth(1).click()
        page.locator('[name="name"]').fill("Edited occupant")
        save_form(page)
        records = wire._service.snapshot()["records"]
        assert next(r for r in records if r["id"] == occupant)["data"]["name"] == "Edited occupant"
        assert (
            next(r for r in records if r["id"] == cabinet)["data"].get("name", "")
            != "Edited occupant"
        )
        page.locator('[data-rack-unit="5"]').focus()
        page.keyboard.press("Shift+F10")
        page.locator(".rack-unit-context > button").nth(0).click()
        assert page.locator('[name="kind"] option[value="rack"]').count() == 0
        page.locator('[name="name"]').fill("Created at U5")
        save_form(page)
        created = next(
            r
            for r in wire._service.snapshot()["records"]
            if r["data"].get("name") == "Created at U5"
        )
        assert created["data"]["location"]["rack"] == cabinet
        assert created["data"]["location"]["unit"] == 5
        page.locator('[data-rack-unit="7"]').click(button="right")
        page.locator(".rack-unit-context > button").nth(1).click()
        page.locator('[name="element"]').select_option(existing)
        save_form(page)
        updated = next(r for r in wire._service.snapshot()["records"] if r["id"] == existing)
        assert updated["data"]["location"]["unit"] == 7
        assert updated["data"]["location"]["rack"] == cabinet
        page.locator('[data-rack-unit="9"]').click(button="right")
        page.locator(".rack-unit-context > button").nth(1).click()
        page.locator('[name="element"]').select_option(existing)
        page.evaluate("window.appDecision = async text => {window.moveQuestion=text; return false}")
        page.locator("#submit").click()
        page.wait_for_function("Boolean(document.querySelector('#detail-error').textContent)")
        assert (
            next(r for r in wire._service.snapshot()["records"] if r["id"] == existing)["data"][
                "location"
            ]["unit"]
            == 7
        )
        assert existing in page.evaluate("window.moveQuestion")
        page.evaluate("window.appDecision = async () => true")
        save_form(page)
        assert (
            next(r for r in wire._service.snapshot()["records"] if r["id"] == existing)["data"][
                "location"
            ]["unit"]
            == 9
        )
        page.locator('[data-rack-unit="10"]').click(button="right")
        page.locator(".rack-unit-context > button").nth(0).click()
        page.locator('[name="kind"]').select_option("tray")
        page.locator('[name="name"]').fill("Two-unit tray")
        page.locator('[name="heightU"]').fill("2")
        save_form(page)
        tray = next(
            r
            for r in wire._service.snapshot()["records"]
            if r["data"].get("name") == "Two-unit tray"
        )
        page.locator('[data-rack-unit="10"]').click(button="right")
        page.locator(f'[data-rack-tray-create="{tray["id"]}"]').click()
        assert set(
            page.locator('[name="kind"] option').evaluate_all("opts => opts.map(o => o.value)")
        ) == {"switch", "router.gateway", "router.otg"}
        page.locator('[name="kind"]').select_option("switch")
        assert set(
            page.locator('[name="rj45Count"] option').evaluate_all("opts => opts.map(o => o.value)")
        ) == {"0", "5", "8"}
        page.locator('[name="rj45Count"]').select_option("5")
        page.locator('[name="sfpCount"]').select_option("0")
        page.locator('[name="name"]').fill("Created inside tray")
        save_form(page)
        hosted = next(
            r
            for r in wire._service.snapshot()["records"]
            if r["data"].get("name") == "Created inside tray"
        )
        assert hosted["data"]["location"]["tray"] == tray["id"]
        assert hosted["data"]["location"]["unit"] == 0
        cabinet_state = next(r for r in rack.bootstrap()["records"] if r["id"] == cabinet)
        placed = next(r for r in cabinet_state["occupants"] if r["id"] == tray["id"])
        assert placed["span"] == 2 and placed["unit"] == 10
        for identifier in small:
            page.locator('[data-rack-unit="10"]').click(button="right")
            page.locator(f'[data-rack-house="{tray["id"]}"]').click()
            page.locator('[name="device"]').select_option(identifier)
            save_form(page)
            child = next(r for r in wire._service.snapshot()["records"] if r["id"] == identifier)
            assert child["data"]["location"]["tray"] == tray["id"]
        cabinet_state = next(r for r in rack.bootstrap()["records"] if r["id"] == cabinet)
        assert all(r["unit"] == 0 for r in cabinet_state["occupants"] if r["id"] in small)
        if skins:
            assert (
                page.locator(f'[data-rack-occupant="{tray["id"]}"]').get_attribute("style")
                == "--rack-span:2"
            )
        else:
            for unit in (10, 11):
                assert (
                    page.locator(f'[data-rack-unit="{unit}"]').get_attribute("data-rack-occupant")
                    == tray["id"]
                )
        before = wire._service.snapshot()["records"]
        page.locator('[data-rack-unit="8"]').click(button="right")
        page.locator(".rack-unit-context > button").nth(0).click()
        page.locator('[name="kind"]').select_option("tray")
        page.locator('[name="heightU"]').fill("2")
        page.locator("#submit").click()
        page.wait_for_function("Boolean(document.querySelector('#detail-error').textContent)")
        assert wire._service.snapshot()["records"] == before
        page.locator("dialog.support-dialog[open] button").first.click()
        page.locator("#cancel").click()
        # Dismissing a modified form asks before discarding its unsaved fields.
        page.wait_for_function("!document.querySelector('#detail').open")
        page.locator('[data-rack-unit="12"]').click(button="right")
        page.locator(".rack-unit-context > button").nth(0).click()
        page.locator('[name="kind"]').select_option("tray")
        page.locator('[name="heightU"]').fill("2")
        page.locator("#submit").click()
        page.wait_for_function("Boolean(document.querySelector('#detail-error').textContent)")
        assert wire._service.snapshot()["records"] == before
        assert not errors
        browser.close()
