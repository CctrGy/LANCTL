"""Optional real browser verification for the installer account assistant."""

import os
from pathlib import Path

import pytest


@pytest.mark.skipif(os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="browser opt-in")
def test_remote_account_form_validates_clears_secrets_and_preserves_existing_accounts(tmp_path):
    from playwright.sync_api import sync_playwright

    root = Path(__file__).resolve().parents[1]
    calls = []
    existing = False
    fail = True

    def rpc(method, args):
        nonlocal fail
        calls.append((method, args))
        if method == "setup_status":
            return {"ok": True, "scope": "service", "hasUsers": existing, "canCreate": not existing}
        if method == "create_initial_user":
            if fail:
                fail = False
                return {"ok": False, "error": "No se pudo crear la cuenta de prueba"}
            return {"ok": True, "created": True, "message": "Cuenta creada"}
        return {"ok": True}

    def open_page(browser):
        page = browser.new_page(viewport={"width": 720, "height": 850})
        page.expose_function("rpc", rpc)
        page.goto((root / "gui/remote-setup.html").as_uri())
        assert page.locator('[type="submit"]').is_disabled()
        page.evaluate(
            "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};"
            "window.dispatchEvent(new Event('pywebviewready'))"
        )
        page.wait_for_function(
            "!document.querySelector('#scope').textContent.includes('Comprobando')"
        )
        return page

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = open_page(browser)
        assert page.locator('[name="username"]').is_enabled()
        assert page.locator("#account-role").inner_text().startswith("Crear esta cuenta no activa")
        assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
        page.screenshot(path=str(tmp_path / "remote-setup-form.png"))
        secret = "temporary-test-secret-42"
        page.locator('[name="username"]').fill("admin-prueba")
        page.locator('[name="password"]').fill(secret)
        page.locator('[name="confirmation"]').fill("different-test-secret")
        page.locator('[type="submit"]').click()
        assert "no coinciden" in page.locator("#status").inner_text()
        assert not any(method == "create_initial_user" for method, _ in calls)
        page.locator('[name="confirmation"]').fill(secret)
        page.locator('[type="submit"]').click()
        page.wait_for_function("document.querySelector('#status').classList.contains('error')")
        assert page.locator('[name="password"]').input_value() == ""
        assert page.locator('[name="confirmation"]').input_value() == ""
        page.locator('[name="password"]').fill(secret)
        page.locator('[name="confirmation"]').fill(secret)
        page.locator('[type="submit"]').click()
        page.locator("#cancel").get_by_text("Finalizar").wait_for()
        assert page.locator('[name="username"]').is_disabled()
        assert page.locator('[type="submit"]').is_hidden()
        assert page.locator('[name="password"]').input_value() == ""
        assert secret not in page.content()
        creations = [args for method, args in calls if method == "create_initial_user"]
        assert creations == [["admin-prueba", secret, secret]] * 2
        page.locator("#cancel").click()
        page.wait_for_timeout(50)
        assert calls[-1][0] == "request_close"
        page.close()
        existing = True
        page = open_page(browser)
        assert "ya tiene cuentas" in page.locator("#scope").inner_text()
        assert page.locator('[name="username"]').is_disabled()
        assert page.locator('[type="submit"]').is_disabled()
        assert len([1 for method, _ in calls if method == "create_initial_user"]) == 2
        page.locator("#cancel").click()
        page.wait_for_timeout(50)
        assert calls[-1][0] == "request_close"
        browser.close()


def test_setup_launches_remote_account_assistant_in_service_scope_without_secret_arguments():
    root = Path(__file__).resolve().parents[1]
    setup = (root / "packaging/inno/LANCTL.iss").read_text(encoding="utf-8")
    line = next(line for line in setup.splitlines() if 'Parameters: "remote-setup"' in line)
    assert "Tasks: remoteaccount" in line
    assert "waituntilterminated skipifsilent" in line
    assert "runasoriginaluser" not in line
    assert "password" not in line.lower()
    assert setup.index('"{sys}\\icacls.exe"') < setup.index(line)


@pytest.mark.skipif(os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="browser opt-in")
def test_remote_assistant_creates_authenticatable_account_through_real_local_api(
    tmp_path, monkeypatch
):
    from playwright.sync_api import sync_playwright

    from lanctl.apps.access import remote_setup
    from lanctl.apps.access.auth import AuthenticationService
    from lanctl.apps.access.store import AccessStore

    monkeypatch.setattr(remote_setup, "require_admin", lambda: None)
    store = tmp_path / "isolated-service" / "users.dc"
    api = remote_setup.RemoteSetupApi(remote_setup.InitialRemoteAccount(store))
    root = Path(__file__).resolve().parents[1]
    password = "isolated-service-test-secret"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 760, "height": 680})
        page.expose_function("rpc", lambda method, args: getattr(api, method)(*args))
        page.goto((root / "gui/remote-setup.html").as_uri())
        page.evaluate(
            "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};"
            "window.dispatchEvent(new Event('pywebviewready'))"
        )
        page.wait_for_function("!document.querySelector('[type=submit]').disabled")
        assert page.evaluate("document.documentElement.scrollHeight <= innerHeight")
        page.locator('[name="username"]').fill("first-admin")
        page.locator('[name="password"]').fill(password)
        page.locator('[name="confirmation"]').fill(password)
        page.locator('[type="submit"]').click()
        page.locator("#cancel").get_by_text("Finalizar").wait_for()
        assert password not in page.content() + store.read_text(encoding="utf-8")
        assert page.locator('[name="password"]').input_value() == ""
        assert not api.setup_status()["canCreate"]
        user = AuthenticationService(AccessStore(store)).authenticate_password(
            "first-admin", password, "127.0.0.1"
        )
        assert user.username == "first-admin" and user.roles == ["administrator"]
        assert not (store.parent / "config.json").exists()
        browser.close()
