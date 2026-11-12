"""P128: shared save action persists physical data and respects project context."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.core import config
from lanctl.core.projects.workspace import activate_project_workspace


@pytest.mark.parametrize("launcher", ["lanwire", "lanrack"])
def test_physical_save_reopens_and_rejects_stale_context(workspace, tmp_path, launcher):
    first, second = projects(workspace, tmp_path)
    service = api(launcher)
    context = service.bootstrap()["projectContext"]
    rack = api("lanwire").wire_create({"kind": "rack", "prefix": "RK", "name": "P128"})
    assert rack["ok"], rack
    if launcher == "lanrack":
        assert service.rack_dimensions(
            service.bootstrap()["organizationRevision"],
            rack["id"],
            {"units": 42, "widthInches": 19},
        )["ok"]
    assert service.project_state()["dirty"]
    result = service.project_call(context, "save_project", [])
    assert result["ok"], result
    assert not service.project_state()["dirty"]
    activate_project_workspace(second)
    before = Path(second).read_bytes()
    stale = service.project_call(context, "save_project", [])
    assert not stale["ok"] and stale["errorId"]
    assert Path(second).read_bytes() == before
    activate_project_workspace(first, root=tmp_path / "reopened", refresh=True)
    rows = service.bootstrap()["records"]
    restored = next(row for row in rows if row["id"] == rack["id"])
    if launcher == "lanrack":
        assert restored["units"] == 42


@pytest.mark.parametrize("launcher", ["lanwire", "lanrack"])
def test_physical_save_failure_retains_dirty_workspace(workspace, tmp_path, launcher):
    projects(workspace, tmp_path)
    service = api(launcher)
    assert api("lanwire").wire_create({"kind": "rack", "prefix": "RK", "name": "Pending"})["ok"]
    before = Path(config.load_config()["activeProject"]).read_bytes()
    with patch(
        "lanctl.core.projects.save_policy.save_active_project",
        side_effect=OSError("P128 injected save failure"),
    ):
        result = service.project_call(service.bootstrap()["projectContext"], "save_project", [])
    assert not result["ok"] and result["errorId"]
    assert "P128 injected save failure" in result["error"]
    assert Path(config.load_config()["activeProject"]).read_bytes() == before
    assert service.project_state()["dirty"]
    assert service.save_project()["ok"]


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
@pytest.mark.parametrize("launcher", ["lanwire", "lanrack"])
@pytest.mark.parametrize("language,label", [("es", "Guardar proyecto"), ("en", "Save project")])
def test_save_button_keyboard_and_reopen(
    workspace, tmp_path, monkeypatch, launcher, language, label
):
    from lanctl.shared.i18n import language_context

    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    first, second = projects(workspace, tmp_path)
    service = api(launcher)
    root = Path(__file__).resolve().parents[1]
    from lanctl.shared import i18n

    manager = i18n.LanguageManager(tmp_path / "languages")
    manager.initialize()
    manager.install(root / "bundled/languages/spanish.lang")
    monkeypatch.setattr(i18n, "_MANAGER", manager)
    settings = config.load_config()
    settings["language"] = language
    config.save_config(settings)
    with language_context(language), playwright() as p:
        browser = p.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 780, "height": 560})
        page.set_default_timeout(10000)
        page.clock.install()
        failures = []
        page.on("pageerror", lambda error: failures.append(str(error)))
        page.expose_function("rpc", lambda method, args: getattr(service, method)(*args))
        page.goto((root / "gui/launcher.html").as_uri())
        page.evaluate("""() => {
          window.pywebview = {api: new Proxy({}, {get: (_, method) =>
            (...args) => rpc(method, args)})};
          window.dispatchEvent(new Event('pywebviewready'));
        }""")
        button = page.locator("#save")
        page.wait_for_function("document.querySelector('#project-name').textContent==='First'")
        assert button.is_visible() and button.is_enabled()
        assert button.inner_text() == label
        bounds = button.bounding_box()
        assert bounds["y"] >= 0 and bounds["y"] + bounds["height"] <= 560
        rack = api("lanwire").wire_create({"kind": "rack", "prefix": "RK", "name": "UI saved"})
        assert rack["ok"]
        page.evaluate("refresh()")
        if launcher == "lanrack":
            page.get_by_role(
                "button",
                name="Editar dimensiones" if language == "es" else "Edit dimensions",
                exact=True,
            ).click()
            page.locator('[name="units"]').fill("42")
            page.locator("#submit").click()
            page.wait_for_function("!document.querySelector('#detail').open")
        page.wait_for_function("!busy && !refreshing")
        page.screenshot(path=str(tmp_path / f"{launcher}-{language}-save.png"))
        button.focus()
        page.keyboard.press("Enter")
        page.wait_for_function("!document.querySelector('#save').disabled")
        page.wait_for_function("document.querySelector('#status').textContent.includes('First')")
        assert not service.project_state()["dirty"]
        # The stale rendered context must not save the newly selected project.
        activate_project_workspace(second)
        second_bytes = Path(second).read_bytes()
        button.click()
        page.wait_for_function("document.querySelector('#status').classList.contains('error')")
        assert Path(second).read_bytes() == second_bytes
        assert button.is_enabled()
        # Refresh without a project: visible disabled button, no accidental save.
        cfg = config.load_config()
        cfg.update(activeProject=None, projectWorkspace=None)
        config.save_config(cfg)
        page.evaluate("refresh()")
        assert button.is_visible() and button.is_disabled()
        assert button.get_attribute("title")
        assert not failures, failures
        browser.close()
    activate_project_workspace(first, root=tmp_path / "ui-reopened", refresh=True)
    restored = next(row for row in service.bootstrap()["records"] if row["id"] == rack["id"])
    if launcher == "lanrack":
        assert restored["units"] == 42
