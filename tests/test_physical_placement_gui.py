"""Real browser regression for placement editing and launcher project labels."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def open_page(browser, service, file="launcher.html", *, init_script=None):
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    if init_script:
        page.add_init_script(init_script)
    page.expose_function("rpc", lambda method, args: getattr(service, method)(*args))
    page.goto((Path(__file__).resolve().parents[1] / "gui" / file).as_uri())
    page.evaluate(
        "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
    )
    return page


def save_form(page):
    page.locator("#submit").click()
    page.wait_for_function("!document.querySelector('#detail').open")


def test_real_rack_editor_tray_movement_and_wire_feedback(workspace):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    tray = wire.wire_create(
        {
            "kind": "tray",
            "prefix": "TR",
            "name": "Bandeja",
            "rack": cabinet,
            "unit": 2,
            "heightU": 2,
        }
    )["id"]
    router = wire.wire_create({"kind": "router.gateway", "prefix": "RT", "name": "Router neutro"})[
        "id"
    ]
    otg = wire.wire_create({"kind": "router.otg", "prefix": "OT", "name": "OTG"})["id"]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, rack)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        page.locator(f'[data-rack-occupant="{tray}"]').click()
        page.get_by_role("button", name="Alojar dispositivo", exact=True).click()
        page.locator("[name=device]").select_option(router)
        save_form(page)
        for identifier in (otg,):
            page.locator(f'[data-physical-element="{identifier}"]').click()
            page.get_by_role("tab", name="Ubicación", exact=True).click()
            page.locator("[name=placement]").select_option("hosted")
            page.locator("[name=tray]").select_option(tray)
            save_form(page)
        assert (
            router in page.locator(f'[data-rack-occupant="{tray}"]').inner_text()
            or "Router neutro" in page.locator(f'[data-rack-occupant="{tray}"]').inner_text()
        )
        page.locator(f'[data-rack-occupant="{tray}"]').click()
        page.get_by_role("button", name="Mover elemento", exact=True).click()
        page.locator("[name=destination]").select_option(f"{cabinet}|5")
        save_form(page)
        rows = wire.bootstrap()["records"]
        assert next(r for r in rows if r["id"] == router)["placement"]["unit"] == 5
        assert next(r for r in rows if r["id"] == otg)["placement"]["tray"] == tray
        assert page.locator(".rack-skin-empty").count() == 10
        page.screenshot(
            path=str(Path(".tool-reports/physical-placement.png").resolve()), full_page=True
        )
        page.locator(f'[data-physical-element="{router}"]').click()
        page.locator("[name=name]").fill("Router editado desde LANRACK")
        save_form(page)
        assert wire._service.database.get(router)["data"]["name"] == "Router editado desde LANRACK"
        # The same classified records and real endpoints are accessible in LANWIRE.
        topology = open_page(browser, wire)
        topology.wait_for_function("state.launcher === 'lanwire'")
        topology.evaluate("id => fullDetails(state.records.find(r=>r.id===id))", router)
        topology.get_by_role("tab", name="Ubicación", exact=True).click()
        assert topology.locator("[name=placement]").input_value() == "hosted"
        topology.locator("[name=placement]").select_option("environment")
        topology.locator("[name=rack]").select_option(cabinet)
        save_form(topology)
        page.evaluate("window.launcherDataChanged=true")
        page.wait_for_function(
            "id => state.elements.some(r=>r.id===id && r.placement.kind==='environment')",
            arg=router,
        )
        assert not errors, errors
        browser.close()


def test_project_selectors_centralized_labels_follow_loaded_data(workspace, tmp_path):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.apps.suite.gui import SuiteApi
    from lanctl.core import config

    _, second = projects(workspace, tmp_path)
    cfg = config.load_config()
    cfg["projectsDirectory"] = str(tmp_path)
    config.save_config(cfg)
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop = DesktopApi()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        pages = [
            open_page(browser, api(name)) for name in ("lanwire", "lanrack", "lanaccess", "lanmon")
        ]
        ip = open_page(browser, desktop, "index.html")
        ip.wait_for_function("desktopReady")
        assert not ip.locator("#project-select").is_visible()
        assert not ip.locator("#project-open").is_visible()
        assert not ip.locator("#project-new").is_visible()
        for page in pages:
            page.locator("footer #project-name").get_by_text("First", exact=True).wait_for()
            assert page.locator("#wire-project").count() == 0
            assert page.locator("#home").is_visible()
        suite = open_page(browser, SuiteApi(), "suite.html")
        suite.locator("#project").select_option(second)
        suite.wait_for_function("path => state.activeProject === path", arg=second)
        for page in pages:
            page.evaluate("window.launcherDataChanged=true")
            page.wait_for_function(
                "document.querySelector('footer #project-name').textContent==='Second'"
            )
            assert page.evaluate("state.projectContext[0]") == second
        ip.evaluate("window.desktopDataChanged=true")
        ip.wait_for_function("document.querySelector('#footer-project').textContent==='Second'")
        assert ip.evaluate("state.projectContext[0]") == second
        browser.close()
