"""Modal settings integration with the real catalog and temporary configuration."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.apps.suite.gui import SuiteApi
from lanctl.core import config

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_full_settings_modal_controls_save_cancel_and_launcher(workspace):
    playwright = pytest.importorskip("playwright.sync_api")
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        api = SuiteApi()
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 1100, "height": 850})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.expose_function("rpc", lambda method, args: getattr(api, method)(*args))
        page.goto((Path(__file__).resolve().parents[1] / "gui/suite.html").as_uri())
        page.evaluate("""async () => {
          window.pywebview={api:new Proxy({}, {get:(_,method)=>(...args)=>rpc(method,args)})};
          await refresh();
        }""")
        page.locator('[data-page="settings"]').click()
        page.locator("#suite-settings").wait_for(state="visible")
        assert page.evaluate("state.page") == "home"
        catalog = api.settings_catalog()["entries"]
        expected = {entry["path"] for entry in catalog if entry["path"] != "access.remote"}
        actual = set(
            page.locator(".ss-card").evaluate_all("cards=>cards.map(card=>card.dataset.path)")
        )
        assert actual == expected
        assert (
            page.locator('[data-path="startup.closeGuiOnLaunch"] input[type="checkbox"]').count()
            == 1
        )
        page.locator("#ss-search").fill("projects.directory")
        folder = str(Path(workspace["database"]).parent)
        with patch.object(
            api, "select_project_directory", return_value={"ok": True, "path": folder}
        ):
            page.get_by_role(
                "button",
                name=page.evaluate("LanctlI18n.t('LANCTL.UI.TEXT.CHOOSE_FOLDER')"),
                exact=True,
            ).click()
            page.wait_for_function(
                "path=>document.querySelector('[data-path=\"projects.directory\"] input[type=text]').value===path",
                arg=folder,
            )
        assert config.load_config()["projectsDirectory"] is None
        page.locator("#ss-search").fill("logging.retentionDays")
        retention = page.locator('[data-path="logging.retentionDays"] input')
        retention.fill("19")
        page.locator("#ss-search").fill("gui.density")
        page.locator('[data-path="gui.density"] select').select_option("compact")
        page.locator("#ss-save").click()
        page.wait_for_function(
            "document.querySelector('#ss-status').textContent===LanctlI18n.t('LANCTL.UI.TEXT.SETTINGS_SAVED')"
        )
        assert config.load_config()["logRetentionDays"] == 19
        assert config.load_config()["guiPreferences"]["density"] == "compact"
        # Validation errors retain every draft and never partially write the batch.
        before = config.CONFIG_PATH.read_bytes()
        page.locator("#ss-search").fill("gui.fontScale")
        page.locator('[data-path="gui.fontScale"] input').fill("-5")
        page.locator("#ss-search").fill("logging.retentionDays")
        retention.fill("22")
        page.locator("#ss-save").click()
        page.wait_for_function("document.querySelector('#ss-status').classList.contains('error')")
        assert config.CONFIG_PATH.read_bytes() == before
        page.locator("#ss-cancel").click()
        page.locator("#confirmation-cancel").click()
        assert page.locator("#suite-settings").is_visible()
        assert retention.input_value() == "22"
        page.locator("#ss-cancel").click()
        page.locator("#confirmation-accept").click()
        page.locator("#suite-settings").wait_for(state="hidden")
        # Launcher gears reuse the same design, restricted to that launcher's catalog.
        page.locator('[data-launcher-settings="lanmon"]').click()
        page.locator("#suite-settings").wait_for(state="visible")
        paths = page.locator(".ss-card").evaluate_all("cards=>cards.map(card=>card.dataset.path)")
        launcher_entries = api.launcher_settings("lanmon")["entries"]
        assert set(paths) == {
            entry["path"] for entry in launcher_entries if entry["path"] != "access.remote"
        }
        assert "ip.workers" not in paths
        for width, height in ((1100, 850), (560, 500), (390, 650)):
            page.set_viewport_size({"width": width, "height": height})
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            bounds = page.locator("#suite-settings").bounding_box()
            assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= width + 1
            assert page.locator("#ss-cancel").is_visible()
        assert not errors
        page.locator("#ss-cancel").click()
        browser.close()


def test_project_scope_uses_typed_controls_and_keeps_original_context(workspace, tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        api = SuiteApi()
    created = api.create_project("First", str(tmp_path))
    assert created["ok"], created
    first = config.load_config()["activeProject"]
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 1100, "height": 850})
        page.expose_function("rpc", lambda method, args: getattr(api, method)(*args))
        page.goto((Path(__file__).resolve().parents[1] / "gui/suite.html").as_uri())
        page.evaluate(
            "async()=>{window.pywebview={api:new Proxy({}, {get:(_,method)=>(...args)=>rpc(method,args)})};await refresh();}"
        )
        page.locator('[data-page="settings"]').click()
        page.locator('[data-ss-scope="project"]').click()
        page.wait_for_function("document.querySelector('#ss-save').hidden")
        expected = {item["path"] for item in api.settings_catalog("project")["entries"]}
        assert (
            set(page.locator(".ss-card").evaluate_all("cards=>cards.map(card=>card.dataset.path)"))
            == expected
        )
        page.locator("#ss-search").fill("identity.name")
        card = page.locator('[data-path="identity.name"]')
        card.locator("input[type=text]").fill("Renamed")
        card.locator(".ss-save-one").click()
        page.wait_for_function(
            "document.querySelector('#ss-status').textContent===LanctlI18n.t('LANCTL.UI.VIEW.PROJECT_SETTING_SAVED')"
        )
        assert api.project_metadata(first)["values"]["name"] == "Renamed"
        page.locator("#ss-search").fill("vlan.nativeVlan")
        assert page.locator('[data-path="vlan.nativeVlan"] input[type=number]').count() == 1
        # Another launcher switches the active project while this form is open.
        second = api.create_project("Second", str(tmp_path))
        assert second["ok"], second
        active = config.load_config()["activeProject"]
        before = Path(active).read_bytes()
        page.locator("#ss-search").fill("identity.description")
        card = page.locator('[data-path="identity.description"]')
        card.locator("input[type=text]").fill("Must not enter the new project")
        card.locator(".ss-save-one").click()
        page.wait_for_function("document.querySelector('#ss-status').classList.contains('error')")
        assert Path(active).read_bytes() == before
        page.locator("#ss-cancel").click()
        page.locator("#confirmation-accept").click()
        browser.close()


def test_settings_keyboard_search_and_all_builtin_themes(workspace):
    playwright = pytest.importorskip("playwright.sync_api")
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        api = SuiteApi()
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 1100, "height": 850})
        page.expose_function("rpc", lambda method, args: getattr(api, method)(*args))
        page.goto((Path(__file__).resolve().parents[1] / "gui/suite.html").as_uri())
        page.evaluate(
            "async()=>{window.pywebview={api:new Proxy({}, {get:(_,method)=>(...args)=>rpc(method,args)})};await refresh();}"
        )
        page.locator('[data-page="settings"]').click()
        search = page.locator("#ss-search")
        search.wait_for(state="visible")
        assert search.evaluate("el=>el===document.activeElement")
        search.fill("no-matching-preference-123")
        assert page.locator("#ss-empty").is_visible()
        search.fill("")
        assert not page.locator("#ss-empty").is_visible()
        first = page.locator("#ss-tabs [role=tab]").first
        first.focus()
        page.keyboard.press("ArrowRight")
        assert page.locator("#ss-tabs [role=tab]").nth(1).get_attribute("aria-selected") == "true"
        page.keyboard.press("End")
        assert page.locator("#ss-tabs [role=tab]").last.get_attribute("aria-selected") == "true"
        page.keyboard.press("Home")
        assert first.get_attribute("aria-selected") == "true"
        for theme in api.gui_preferences()["themes"]:
            assert api.save_catalog_settings({"gui.theme": theme["id"]})["ok"]
            page.evaluate("guiAppearance.sync()")
            expected = theme["tokens"]["--color-background"]
            assert (
                page.evaluate(
                    "getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()"
                )
                == expected
            )
            for width, height in ((1100, 850), (560, 500), (390, 650)):
                page.set_viewport_size({"width": width, "height": height})
                assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                assert page.locator("#ss-cancel").is_visible()
                assert page.locator("#ss-save").is_visible()
            if theme["id"] == "light":
                page.set_viewport_size({"width": 1100, "height": 850})
                page.screenshot(path="/tmp/lanctl-settings-light.png", full_page=True)
        page.locator("#ss-close").click()
        assert not page.locator("#suite-settings").is_visible()
        browser.close()
