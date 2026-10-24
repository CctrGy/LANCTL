"""P83: clock-free footers without losing refresh, context or diagnostic dates."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
from lanctl.apps.monitor.database import IncidentRepository, MonitorDatabase
from lanctl.apps.monitor.models import Incident
from lanctl.apps.suite.gui import SuiteApi
from lanctl.core import config
from lanctl.core.database import DeviceDatabase
from lanctl.core.history import HistoryEvent, HistoryService
from lanctl.core.paths import application_path
from lanctl.core.session import Session

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def browser():
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        instance = p.chromium.launch(channel="msedge", headless=True)
        yield instance
        instance.close()


def connect(browser, service, filename="launcher.html"):
    page = browser.new_page(viewport={"width": 1440, "height": 900}, timezone_id="Europe/Madrid")
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.clock.install()
    page.expose_function("rpc", lambda method, args: getattr(service, method)(*args))
    page.goto((ROOT / "gui" / filename).as_uri())
    page.evaluate(
        """() => {
          window.completedCalls = [];
          window.pywebview = {api: new Proxy({}, {get: (_, method) => async (...args) => {
            const result = await rpc(method, args);
            completedCalls.push(method);
            return result;
          }})};
          window.dispatchEvent(new Event('pywebviewready'));
        }"""
    )
    return page, errors


@pytest.mark.parametrize(
    "launcher", ["lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"]
)
def test_footers_keep_context_navigation_and_background_refresh(
    workspace, tmp_path, browser, launcher
):
    projects(workspace, tmp_path)
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        service = (
            SuiteApi()
            if launcher == "lanctl"
            else DesktopApi()
            if launcher == "lanip"
            else api(launcher)
        )
    filename = (
        "suite.html"
        if launcher == "lanctl"
        else "index.html"
        if launcher == "lanip"
        else "launcher.html"
    )
    project = (
        "#project-status"
        if launcher == "lanctl"
        else "#footer-project"
        if launcher == "lanip"
        else "#project-name"
    )
    navigation = (
        ["#external-cli"]
        if launcher == "lanctl"
        else ["#lanctl-gui", "#lanip-cli"]
        if launcher == "lanip"
        else ["#home", "#cli"]
    )
    page, errors = connect(browser, service, filename)
    page.locator("footer " + project).get_by_text("First", exact=False).wait_for()
    if launcher == "lanip":
        page.wait_for_function("desktopReady")
    for width, height in ((1440, 900), (800, 600)):
        page.set_viewport_size({"width": width, "height": height})
        assert page.locator("footer time, #clock").count() == 0
        # LANIP stacks the inventory in small windows and scrolls the document.
        page.locator("footer").scroll_into_view_if_needed()
        footer = page.locator("footer").bounding_box()
        assert footer["y"] >= 0 and footer["y"] + footer["height"] <= height + 1
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        for selector in [project, *navigation]:
            control = page.locator(selector)
            assert control.is_visible()
            bounds = control.bounding_box()
            assert bounds["x"] >= 0 and bounds["x"] + bounds["width"] <= width + 1
    # Advance past the old clock interval: removing it must not disable refresh.
    method = "sync_project" if launcher == "lanip" else "bootstrap"
    count = page.evaluate("method => completedCalls.filter(m => m === method).length", method)
    if launcher == "lanctl":
        page.evaluate("window.suiteDataChanged = true")
    elif launcher == "lanip":
        page.evaluate("window.desktopDataChanged = true")
    page.clock.fast_forward(6100)
    page.wait_for_function(
        "([method, count]) => completedCalls.filter(m => m === method).length > count",
        arg=[method, count],
    )
    assert "First" in page.locator("footer " + project).inner_text()
    assert page.locator("footer time, #clock").count() == 0
    assert not errors, errors
    page.screenshot(path=str(ROOT / ".tool-reports" / f"p83-{launcher}-footer.png"))


def test_monitor_preserves_event_incident_activity_and_log_dates(
    workspace, tmp_path, monkeypatch, browser
):
    first, _ = projects(workspace, tmp_path)
    active = config.load_config()
    device = DeviceDatabase(active["database"]).upsert(
        [{"IP": "192.0.2.10", "MAC": "02:00:00:00:00:10"}]
    )[0]
    stamp = "2026-10-18T10:42:18+02:00"
    event = HistoryEvent(
        "device.detected",
        "lanctl.monitor",
        "local",
        "success",
        "Evento histórico P83",
        timestamp=stamp,
    )
    history = HistoryService(first)
    history.write(event)
    with MonitorDatabase(application_path(active["monitorDatabase"])) as db:
        IncidentRepository(db).save(
            Incident(
                "incident-p83",
                device.device_id,
                "warning",
                "Incidencia histórica P83",
                "test",
                stamp,
            )
        )
    log = application_path(active["programLog"]) / "18-10-2026.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text("[10:39:04] Registro histórico P83\n", encoding="utf-8")
    saved_log = log.read_bytes()
    session = Session("lanctl", "gui", active)
    monkeypatch.setattr("lanctl.core.session._current", session)
    try:
        suite, monitor = SuiteApi(), api("lanmon")
        activity = suite.record_activity("Actividad P83")["activity"]
        page, errors = connect(browser, monitor)
        page.locator(".aside").get_by_text(stamp, exact=False).wait_for()
        assert page.locator(".event time").inner_text() == "10:42"
        page.locator('[data-monitor-page="activity"]').click()
        entry = page.locator("#monitor-evidence article").filter(has_text="Actividad P83")
        entry.wait_for()
        assert str(activity["created"]) in entry.locator("small").inner_text()
        page.locator('[data-monitor-page="logs"]').click()
        entry = page.locator("#monitor-evidence article").filter(has_text="Registro histórico P83")
        entry.wait_for()
        assert "18-10-2026.log" in entry.locator("small").inner_text()
        assert "[10:39:04]" in entry.locator("pre").inner_text()
        assert log.read_bytes() == saved_log
        assert history.query(search="Evento histórico P83")[0].timestamp == stamp
        assert page.locator("footer time, #clock").count() == 0
        assert not errors, errors
    finally:
        session.close()


def test_prototype_footers_without_clock_preserve_sample_event_times(browser):
    page = browser.new_page(viewport={"width": 800, "height": 600})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    for launcher in ("wire", "rack", "access", "mon"):
        # Each fragment is a direct start, not an in-page hash change.
        page.goto("about:blank")
        page.goto((ROOT / "gui/launcher-prototypes.html").as_uri() + "#" + launcher)
        page.locator("#footer-app").get_by_text("LAN" + launcher.upper(), exact=True).wait_for()
        assert page.locator("footer time, #clock").count() == 0
        assert page.locator("#home").is_visible() and page.locator("#cli").is_visible()
        if launcher == "mon":
            assert page.locator(".event time").all_text_contents() == [
                "10:42:18",
                "10:39:04",
                "10:34:52",
            ]
    assert not errors, errors
