"""P82 browser regressions with real services and isolated stores."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page, save_form
from test_project_sync import projects
from test_view_editing import credential, inventory, row

from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
from lanctl.core import config
from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.workspace import activate_project_workspace

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def discard(page):
    page.locator("#cancel").click()
    page.locator("#app-notice-accept").click()
    page.wait_for_function("!document.querySelector('#detail').open")


def test_monitor_edits_cancel_groups_filters_and_feedback_with_lanip(workspace):
    database, device, _ = inventory(workspace)
    database.set_alias(device.device_id, "Original")
    monitor = api("lanmon")
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop = DesktopApi()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, monitor)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.locator("#search").fill("Original")
        page.locator(f'[data-id="{device.device_id}"]').dblclick()
        page.locator("[name=alias]").fill("Cancelado")
        page.locator("#cancel").click()
        page.locator("#app-notice-cancel").click()
        assert page.locator("[name=alias]").input_value() == "Cancelado"
        discard(page)
        assert database.resolve(device.device_id).alias == "Original"
        page.locator(f'[data-id="{device.device_id}"]').dblclick()
        page.locator("[name=alias]").fill("Nuevo alias")
        save_form(page)
        assert database.resolve(device.device_id).alias == "Nuevo alias"
        assert page.locator("#search").input_value() == "Original"
        assert page.locator(f'[data-id="{device.device_id}"].selected').count() == 1
        assert page.locator(".record-editor-retained").is_visible()
        # The LANIP sheet reads and edits the same data, without running probes.
        lanip = open_page(browser, desktop, file="index.html")
        lanip.locator(f'[data-device-id="{device.device_id}"]').dblclick()
        lanip.locator("#tab-edit").click()
        assert lanip.locator("#edit-alias").input_value() == "Nuevo alias"
        lanip.locator("#edit-alias").fill("Desde LANIP")
        lanip.locator("#save-device").click()
        lanip.get_by_text("Cambios guardados.", exact=True).wait_for()
        page.evaluate("window.launcherDataChanged=true")
        page.locator(f'[data-id="{device.device_id}"]').get_by_text(
            "Desde LANIP", exact=True
        ).wait_for()
        page.locator(f'[data-id="{device.device_id}"]').dblclick()
        page.get_by_role("tab", name="Observaciones", exact=True).click()
        assert page.locator("[name=latency],[name=presence],[name=health]").count() == 0
        assert "4.2 ms" in page.locator("#detail-fields").inner_text()
        page.get_by_role("tab", name="Datos", exact=True).click()
        page.locator("[name=alias]").fill("Sin guardar")
        page.get_by_role("tab", name="Grupos", exact=True).click()
        page.get_by_role("button", name="Añadir", exact=True).click()
        assert "Guarda o descarta" in page.locator("#detail-error").inner_text()
        assert not database.resolve(device.device_id).groups
        page.get_by_role("tab", name="Datos", exact=True).click()
        page.locator("[name=alias]").fill("Desde LANIP")
        page.get_by_role("tab", name="Grupos", exact=True).click()
        assert page.locator("[name=group] option[value=BASIC]").count() == 0
        page.locator("[name=group]").select_option("LAB")
        page.get_by_role("button", name="Añadir", exact=True).click()
        page.get_by_role("button", name="Retirar de LAB", exact=True).wait_for()
        assert database.resolve(device.device_id).groups == ["LAB"]
        page.screenshot(path=str(Path(".tool-reports/p82-monitor-groups.png").resolve()))
        page.locator("#cancel").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        page.locator("#search").fill("")
        assert page.locator(".record-editor-retained").count() == 0
        assert not errors, errors
        browser.close()


def test_credential_sheet_keeps_secrets_and_rejects_stale_form(workspace):
    access, _, _, identifier = credential(workspace)
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, access)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.locator("#search").fill("operator")
        page.locator(f'[data-id="{identifier}"]').dblclick()
        assert page.locator("[name=password]").is_hidden()
        assert page.locator("[name=password]").input_value() == ""
        assert page.locator("[name=device],[name=protocol],[name=credentialId]").count() == 0
        page.locator("[name=username]").fill("Discarded")
        discard(page)
        assert row(access)["username"] == "operator"
        page.locator(f'[data-id="{identifier}"]').dblclick()
        page.locator("[name=username]").fill("Updated")
        save_form(page)
        assert access._service.manager.store.get(identifier)["password"] == "old-secret"
        assert page.locator(f'[data-id="{identifier}"].selected').count() == 1
        assert page.locator("#search").input_value() == "operator"
        page.locator(f'[data-id="{identifier}"]').dblclick()
        page.locator("[name=rotate]").check()
        page.locator("[name=password]").fill("new-secret")
        page.locator("[name=confirmation]").fill("new-secret")
        save_form(page)
        assert access._service.manager.store.get(identifier)["password"] == "new-secret"
        page.locator(f'[data-id="{identifier}"]').dblclick()
        assert page.locator("[name=password]").input_value() == ""
        page.locator("[name=username]").fill("Obsolete")
        current = row(access)
        assert access.access_update(identifier, current["revision"], {"username": "Other session"})[
            "ok"
        ]
        page.locator("#submit").click()
        page.wait_for_function(
            "document.querySelector('#detail-error').textContent.includes('cambió')"
        )
        assert row(access)["username"] == "Other session"
        assert access._service.manager.store.get(identifier)["password"] == "new-secret"
        page.locator('[data-error="close"]').click()
        assert page.locator("[name=username]").input_value() == "Obsolete"
        discard(page)
        page.locator("#search").fill("")
        page.get_by_role("button", name="Actualizar", exact=True).click()
        page.locator(f'[data-id="{identifier}"]').get_by_text(
            "Other session", exact=True
        ).wait_for()
        page.locator(f'[data-id="{identifier}"]').dblclick()
        page.screenshot(path=str(Path(".tool-reports/p82-credential.png").resolve()))
        assert not errors, errors
        browser.close()


def test_monitor_form_does_not_follow_project_switch_on_save(workspace, tmp_path):
    _, second = projects(workspace, tmp_path)
    active = config.load_config()
    database, device, _ = inventory(active)
    monitor = api("lanmon")
    assert monitor.save_project()["ok"]
    before = database.path.read_bytes()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, monitor)
        page.locator(f'[data-id="{device.device_id}"]').dblclick()
        page.locator("[name=alias]").fill("Wrong project")
        activate_project_workspace(second)
        page.locator("#submit").click()
        page.wait_for_function(
            "document.querySelector('#detail-error').textContent.includes('proyecto cambió')"
        )
        assert database.path.read_bytes() == before
        assert not DeviceDatabase(config.load_config()["database"]).load()
        assert page.locator("[name=alias]").input_value() == "Wrong project"
        browser.close()


def test_cancelled_record_load_cannot_replace_another_dialog(workspace):
    _, device, _ = inventory(workspace)
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser, api("lanmon"))
        page.locator(f'[data-id="{device.device_id}"]').wait_for()
        page.evaluate(
            """() => {
              const original = window.pywebview.api;
              window.pywebview.api = new Proxy(original, {get(target, name) {
                if (name !== 'project_call') return target[name];
                return async (...args) => {
                  const result = await target.project_call(...args);
                  if (args[1] !== 'monitor_device') return result;
                  return new Promise(resolve => {window.deliverRecord = () => resolve(result)});
                };
              }});
            }"""
        )
        page.locator(f'[data-id="{device.device_id}"]').dblclick()
        page.wait_for_function("!!window.deliverRecord")
        page.locator("#cancel").click()
        page.locator("#settings").click()
        page.get_by_role("heading", name="Configuración · LANMON", exact=True).wait_for()
        page.evaluate("window.deliverRecord()")
        page.evaluate("() => new Promise(resolve => requestAnimationFrame(resolve))")
        assert page.locator("#detail-title").inner_text() == "Configuración · LANMON"
        assert page.locator("[name=alias]").count() == 0
        browser.close()
