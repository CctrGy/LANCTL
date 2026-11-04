"""A stop request stays pending in the real launcher UI and temporary backend."""

import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.apps.monitor.database import MonitorDatabase, SessionRepository
from lanctl.apps.monitor.models import MonitorSession
from lanctl.apps.suite.gui import SuiteApi
from lanctl.apps.suite.launcher_gui import LauncherApi
from lanctl.core import config
from lanctl.shared.i18n import ENGLISH_STRINGS, SPANISH_STRINGS

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


@pytest.mark.parametrize("language,strings", [("en", ENGLISH_STRINGS), ("es", SPANISH_STRINGS)])
def test_pending_stop_is_not_presented_as_completed(
    workspace, tmp_path, monkeypatch, language, strings
):
    from lanctl.apps.monitor import commands
    from lanctl.apps.suite import launcher_gui

    playwright = pytest.importorskip("playwright.sync_api")
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        suite = SuiteApi()
    assert suite.create_project("Monitor", str(tmp_path))["ok"]
    settings = config.load_config()
    owner = MonitorSession(
        "session",
        "run",
        "manager",
        settings["activeProject"],
        "",
        "",
        "",
        "permanent",
        "observe",
        "2026-11-03T00:00:00+00:00",
        status="active",
    )
    with MonitorDatabase(settings["monitorDatabase"]) as database:
        SessionRepository(database).save(owner)
    signals = []
    monkeypatch.setattr(
        commands,
        "SingletonLock",
        lambda path: SimpleNamespace(status=lambda: {"running": True, "pid": 12345}),
    )
    monkeypatch.setattr(
        commands,
        "os",
        SimpleNamespace(
            **{**vars(commands.os), "kill": lambda pid, sig: signals.append((pid, sig))}
        ),
    )
    monkeypatch.setattr(
        launcher_gui,
        "initialize_language",
        lambda: SimpleNamespace(
            presentation_payload=lambda: {"code": language, "strings": strings}
        ),
    )
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        api = LauncherApi("lanmon")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        try:
            page = browser.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.expose_function("rpc", lambda method, args: getattr(api, method)(*args))
            page.goto((Path(__file__).resolve().parents[1] / "gui/launcher.html").as_uri())
            page.evaluate("""() => {
                window.pywebview={api:new Proxy({}, {get:(_,method)=>(...args)=>rpc(method,args)})};
                window.dispatchEvent(new Event('pywebviewready'));
            }""")
            page.wait_for_function("state.launcher==='lanmon'&&!refreshing")
            page.locator('[data-action="stop"]').click()
            page.locator("#app-notice-accept").click()
            page.wait_for_function(
                "expected=>document.querySelector('#status').textContent===expected",
                arg=strings["LANCTL.MONITOR.EXECUTION.STOP_REQUESTED"],
            )
            page.wait_for_function(
                "expected=>document.querySelector('#canvas').textContent.includes(expected)",
                arg=strings["LANCTL.MONITOR.EXECUTION.STOPPING"],
            )
            assert (
                strings["LANCTL.MONITOR.EXECUTION.STOPPING"] in page.locator("#canvas").inner_text()
            )
            page.screenshot(path=str(tmp_path / "pending-stop.png"))
            assert (
                strings["LANCTL.UI.FRAGMENT.OPERATION_COMPLETED"]
                not in page.locator("#status").inner_text()
            )
            assert errors == [] and signals
        finally:
            browser.close()
    with MonitorDatabase(settings["monitorDatabase"]) as database:
        assert SessionRepository(database).get(owner.sessionId).status == "stopping"
