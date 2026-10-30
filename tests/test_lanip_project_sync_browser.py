"""LANIP project display and inventory must follow the actual shared selection."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
from lanctl.apps.suite.gui import SuiteApi
from lanctl.core import config
from lanctl.core.database import DeviceDatabase

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


@pytest.mark.parametrize("guard", [None, "editor", "modal", "scan"])
def test_lanip_bootstrap_and_live_project_change(workspace, tmp_path, guard):
    playwright = pytest.importorskip("playwright.sync_api")
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        suite, lanip = SuiteApi(), DesktopApi()
    assert suite.create_project("First", str(tmp_path))["ok"]
    first = config.load_config()["activeProject"]
    DeviceDatabase(config.load_config()["database"]).add_manual_device(alias="First device")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page()
        page.expose_function("rpc", lambda method, args: getattr(lanip, method)(*args))
        page.goto((Path(__file__).resolve().parents[1] / "gui/index.html").as_uri())
        page.evaluate("""() => {
          window.pywebview={api:new Proxy({}, {get:(_,method)=>(...args)=>rpc(method,args)})};
          window.dispatchEvent(new Event('pywebviewready'));
        }""")
        page.wait_for_function("path=>state.projectContext?.[0]===path", arg=first)
        assert page.locator("#footer-project").inner_text() == "First"
        page.wait_for_function(
            "document.querySelector('#device-rows').textContent.includes('First device')"
        )
        assert "First device" in page.locator("#device-rows").inner_text()
        assert not page.evaluate("editorDirty()")
        if guard == "editor":
            page.evaluate("$('#edit-alias').value='Draft alias'")
        elif guard == "modal":
            page.evaluate(
                "showForm('Pending form',[{key:'note',label:'Note',value:'Draft'}],async()=>{})"
            )
        elif guard == "scan":
            page.evaluate("setBusy(true,'Escaneando la red…')")
        assert suite.save_project()["ok"]
        assert suite.create_project("Second", str(tmp_path))["ok"]
        second = config.load_config()["activeProject"]
        DeviceDatabase(config.load_config()["database"]).add_manual_device(alias="Second device")
        if guard:
            page.evaluate("window.desktopDataChanged=true")
            page.wait_for_timeout(1300)
            assert page.evaluate("state.projectContext[0]") == first
            if guard == "editor":
                assert page.locator("#edit-alias").input_value() == "Draft alias"
                page.evaluate("$('#edit-alias').value=state.devices[0].alias")
            elif guard == "modal":
                assert page.locator("#desktop-fields input").input_value() == "Draft"
                page.locator("#desktop-dismiss").click()
            elif guard == "scan":
                page.evaluate("setBusy(false)")
        # Reproduce a dropped notification: shared selection must still converge.
        page.wait_for_function("path=>state.projectContext?.[0]===path", arg=second, timeout=8000)
        assert page.locator("#footer-project").inner_text() == "Second"
        page.wait_for_function(
            "document.querySelector('#device-rows').textContent.includes('Second device')"
        )
        assert "Second device" in page.locator("#device-rows").inner_text()
        assert "First device" not in page.locator("#device-rows").inner_text()
        browser.close()
