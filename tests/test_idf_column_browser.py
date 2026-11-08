"""Optional real-browser regression for the LANIP IDF column."""

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_idf_column_defaults_legacy_preferences_and_persistence():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page()
        page.goto((Path(__file__).resolve().parents[1] / "gui/index.html").as_uri())
        page.evaluate("""() => {
            localStorage.clear(); setupColumns();
            renderInventory({devices:[{id:'device',idf:'AB-12',ip:'192.0.2.1',
                groups:[],protocols:[],active:true}]});
        }""")
        header = page.locator('th[data-column="idf"]')
        cell = page.locator('td[data-column="idf"]')
        toggle = page.locator('[data-column-toggle="idf"]')
        assert header.is_hidden() and cell.is_hidden()
        assert not toggle.is_checked()
        page.evaluate("""() => {
            localStorage.setItem('lanctl.columns', JSON.stringify({mac:false,alias:true}));
            setupColumns();
        }""")
        assert not toggle.is_checked() and header.is_hidden()
        assert page.locator('th[data-column="mac"]').is_hidden()
        page.locator(".column-menu summary").click()
        toggle.check()
        assert cell.is_visible() and cell.inner_text() == "AB-12"
        page.reload()
        page.evaluate("""() => {
            setupColumns(); renderInventory({devices:[{id:'device',idf:'AB-12',
                groups:[],protocols:[],active:true}]});
        }""")
        assert toggle.is_checked() and cell.is_visible()
        assert page.locator('th[data-column="mac"]').is_hidden()
        page.locator(".column-menu summary").click()
        toggle.uncheck()
        assert header.is_hidden() and cell.is_hidden()
        page.evaluate("setupColumns()")
        assert not toggle.is_checked()
        browser.close()
