"""Visible LANWIRE creation actions with real temporary project services."""

import os

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page, save_form
from test_project_sync import projects

from lanctl.core.projects.workspace import activate_project_workspace

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_wire_creation_cancel_connections_cpd_feedback_and_reopen(workspace, tmp_path):
    first, second = projects(workspace, tmp_path)
    wire, rack = api("lanwire"), api("lanrack")
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page, rack_page = open_page(browser, wire), open_page(browser, rack)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        for text in ("Nuevo elemento", "Nuevo cable", "Nuevo rack", "Nuevo CPD"):
            page.get_by_role("button", name=text, exact=True).wait_for()
        page.get_by_role("button", name="Nuevo CPD", exact=True).click()
        page.locator("[name=name]").fill("Cancelar CPD")
        page.locator("#cancel").click()
        page.locator("#app-notice-accept").click()
        assert wire.bootstrap()["cpds"] == []
        page.get_by_role("button", name="Nuevo CPD", exact=True).click()
        page.locator("[name=name]").fill("Sala First")
        save_form(page)
        room = wire.bootstrap()["cpds"][0]["id"]
        page.get_by_role("button", name="Nuevo rack", exact=True).click()
        page.locator("[name=name]").fill("Armario")
        page.locator("[name=units]").fill("12")
        save_form(page)
        page.get_by_role("button", name="Cambiar CPD", exact=True).click()
        page.locator("[name=id]").select_option(room)
        save_form(page)
        ids = []
        for kind, name in (("switch.5ports", "Switch"), ("pc.1port", "PC")):
            page.get_by_role("button", name="Nuevo elemento", exact=True).click()
            page.locator("[name=kind]").select_option(kind)
            page.locator("[name=name]").fill(name)
            save_form(page)
            ids.append(
                next(r["id"] for r in wire.bootstrap()["records"] if r["data"].get("name") == name)
            )
        page.get_by_role("button", name="Nuevo cable", exact=True).click()
        page.locator("[name=name]").fill("Enlace")
        page.locator("[name=endpointA]").select_option(label="Switch · X1")
        page.locator("[name=endpointB]").select_option(label="PC · LAN1")
        save_form(page)
        cable = next(r for r in wire.bootstrap()["records"] if r["data"].get("name") == "Enlace")
        assert cable["data"]["endpoints"] == [
            {"device": ids[0], "port": "X1"},
            {"device": ids[1], "port": "LAN1"},
        ]
        assert page.locator(f'tr[data-id="{cable["id"]}"]').is_visible()
        page.get_by_role("button", name="Editar CPD", exact=True).click()
        page.get_by_role("button", name="Sala First", exact=True).click()
        page.locator("[name=name]").fill("Sala editada")
        save_form(page)
        rack_page.evaluate("window.launcherDataChanged=true")
        rack_page.wait_for_function("state.cpds.some(c=>c.name==='Sala editada')")
        assert len(rack.bootstrap()["elements"]) == 4
        assert wire.save_project()["ok"]
        activate_project_workspace(second)
        assert wire.bootstrap()["records"] == []
        activate_project_workspace(first, root=tmp_path / "reopened")
        assert wire.bootstrap()["cpds"][0]["name"] == "Sala editada"
        assert (
            next(r for r in wire.bootstrap()["records"] if r["id"] == cable["id"])["data"]
            == cable["data"]
        )
        assert not errors, errors
        browser.close()
