"""Exercise the manual creation form on the real LANIP page (Chromium)."""

import os
from pathlib import Path

import pytest

from lanctl.shared.i18n import SPANISH_STRINGS

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_search_create_cancel_validation_and_responsive_layout():
    playwright = pytest.importorskip("playwright.sync_api")
    labels = {
        key.removeprefix("LANCTL.INVENTORY.MANUAL."): value
        for key, value in SPANISH_STRINGS.items()
        if key.startswith("LANCTL.INVENTORY.MANUAL.")
    }
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((Path(__file__).resolve().parents[1] / "gui/index.html").as_uri())
        page.evaluate(
            """labels => {
          window.created=[];window.rejectCreate=false;
          window.snapshot={ok:true,devices:[],summary:{},manualDeviceLabels:labels,
            projectContext:['','test','identity'],projectActions:['create_device']};
          window.pywebview={api:{list_devices:async()=>snapshot,sync_project:async()=>snapshot,project_call:async(expected,method,args)=>{
            if(rejectCreate)return {ok:false,error:'IP en uso'};
            created.push({expected,method,args});
            return {...snapshot,createdId:'manual',message:'Añadido'};
          }}};
          desktopReady=true;renderInventory(snapshot);
        }""",
            labels,
        )
        search = page.locator("#device-search")
        search.fill("192.0.2.10")
        search.press("Enter")
        assert page.evaluate("created.length") == 0
        page.locator("#create-device").click()
        assert page.locator('#desktop-fields input[name="ip"]').input_value() == "192.0.2.10"
        page.locator("#desktop-dismiss").click()
        assert page.evaluate("created.length") == 0
        page.locator("#create-device").click()
        page.locator('#desktop-fields input[name="idf"]').fill("AB-12")
        page.evaluate("rejectCreate=true")
        page.locator("#desktop-form button[type=submit]").click()
        page.wait_for_function("document.querySelector('#desktop-error').textContent==='IP en uso'")
        assert page.locator("#desktop-dialog").is_visible()
        page.evaluate("rejectCreate=false")
        page.locator("#desktop-form button[type=submit]").click()
        page.wait_for_function("created.length===1")
        assert page.evaluate("created[0].args[0].mac") == ""
        assert page.evaluate("created[0].args[0].idf") == "AB-12"
        assert search.input_value() == ""
        for width in (1280, 760, 390):
            page.set_viewport_size({"width": width, "height": 844})
            page.locator("#create-device").scroll_into_view_if_needed()
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        page.set_viewport_size({"width": 1280, "height": 800})
        page.locator("#create-device").click()
        page.screenshot(path="/tmp/lanctl-manual-device.png", full_page=True)
        assert not errors
        browser.close()
