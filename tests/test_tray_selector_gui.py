"""P133: empty tray inventory, direct creation and confirmed relocation."""

import os

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page, save_form

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_empty_selector_create_small_devices_and_move(workspace, tmp_path):
    from test_project_sync import projects

    project, _ = projects(workspace, tmp_path)
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    trays = [
        wire.wire_create(
            {"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": unit, "heightU": 2}
        )["id"]
        for unit in (2, 6)
    ]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, rack)
        page.set_default_timeout(7000)
        page.locator(f'[data-rack-open="{cabinet}"]').click()

        def open_selector(unit, tray):
            page.locator(f'[data-rack-unit="{unit}"]').click(button="right")
            page.locator(f'[data-rack-house="{tray}"]').click()

        open_selector(2, trays[0])
        assert page.locator("[name=device] option").count() == 0
        assert page.locator("[data-tray-hint]").inner_text()
        assert page.locator("#submit").is_hidden()
        created = []
        for index, kind in enumerate(("router.gateway", "router.otg", "switch")):
            page.locator(f'[data-tray-create="{trays[0]}"]').click()
            choices = page.locator("[name=kind] option").evaluate_all(
                "(options)=>options.map(o=>o.value)"
            )
            assert "router.gateway" in choices and "router.otg" in choices and "switch" in choices
            page.locator("[name=kind]").select_option(kind)
            if kind == "switch":
                page.locator("[name=rj45Count]").select_option("5")
                page.locator("[name=sfpCount]").select_option("0")
            page.locator("[name=name]").fill(f"Small {index}")
            save_form(page)
            record = next(
                r for r in wire.bootstrap()["records"] if r["data"].get("name") == f"Small {index}"
            )
            assert record["data"]["location"]["tray"] == trays[0]
            created.append(record)
            open_selector(2, trays[0])
            assert page.locator(f'[name=device] option[value="{record["id"]}"]').count() == 0
        page.locator("#cancel").click()
        open_selector(6, trays[1])
        options = page.locator("[name=device] option").evaluate_all(
            "(options)=>options.map(o=>o.value)"
        )
        assert set(options) == {r["id"] for r in created}
        page.locator("[name=device]").select_option(created[0]["id"])
        page.evaluate("window.appDecision=async text=>{window.question=text;return false}")
        page.locator("#submit").click()
        page.wait_for_function('Boolean(document.querySelector("#detail-error").textContent)')
        assert created[0]["id"] in page.evaluate("window.question")
        assert (
            next(r for r in wire.bootstrap()["records"] if r["id"] == created[0]["id"])["data"][
                "location"
            ]["tray"]
            == trays[0]
        )
        page.evaluate("window.appDecision=async()=>true")
        save_form(page)
        moved = next(r for r in wire.bootstrap()["records"] if r["id"] == created[0]["id"])
        assert moved["data"]["location"]["tray"] == trays[1]
        assert moved["data"]["ports"] == created[0]["data"]["ports"]
        from lanctl.apps.wire.idf.database import IDFDatabaseManager
        from lanctl.core.projects.save_policy import save_active_project
        from lanctl.core.projects.workspace import prepare_project_workspace

        assert save_active_project(force=True).saved
        reopened = prepare_project_workspace(project, root=tmp_path / "reopened")
        from lanctl.core.projects.physical import workspace_path

        persisted = IDFDatabaseManager(workspace_path(reopened.database)).all()
        assert (
            next(r for r in persisted if r["id"] == moved["id"])["data"]["location"]["tray"]
            == trays[1]
        )
        browser.close()
