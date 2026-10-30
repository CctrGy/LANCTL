"""Shared desktop controls against real preferences and activity storage."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import workspace as workspace

from lanctl.apps.suite.gui import SuiteApi
from lanctl.core.session import Session

pytest_plugins = ["test_launcher_gui"]


def test_preferences_shared_by_suite_launchers_and_reopen(workspace):
    from test_launcher_gui import api

    suite = SuiteApi()
    original = suite.gui_preferences()
    assert original["ok"] and len(original["themes"]) == 5
    values = {"theme": "light", "density": "compact", "fontScale": 1.2, "reducedMotion": True}
    assert suite.save_gui_preferences(values)["preferences"] == values
    for name in ("lanwire", "lanrack", "lanaccess", "lanmon"):
        assert api(name).gui_preferences()["preferences"] == values
    assert not suite.save_gui_preferences({**values, "theme": "unknown"})["ok"]
    assert SuiteApi().gui_preferences()["preferences"] == values


def test_activity_uses_registered_session_and_opens_correct_monitor_view(workspace, monkeypatch):
    from test_launcher_gui import api

    session = Session("lanctl", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    try:
        suite = SuiteApi()
        result = suite.record_activity("Operación de interfaz", 43)
        assert result["ok"] and result["activity"]["session"] == session.id
        assert result["activity"]["launcher"] == "lanctl"
        monitor = api("lanmon")
        records = monitor.monitor_activity(all_projects=True)["records"]
        assert any(r["message"] == "Operación de interfaz" for r in records)
        operational = monitor.monitor_logs()["records"]
        assert any(
            "GUI_ACTIVITY" in r["message"]
            and r["level"] == 43
            and "Operación de interfaz" in r["message"]
            for r in operational
        )
        assert not api("lanwire").monitor_activity()["ok"]
        with patch("lanctl.apps.suite.gui_support.subprocess.Popen") as launch:
            assert suite.open_monitor("report")["ok"]
            assert launch.call_args.kwargs["env"]["LANCTL_GUI_VIEW"] == "report"
            assert launch.call_args.kwargs["env"]["LANCTL_GUI_SOURCE_SESSION"] == session.id
            assert not launch.call_args.kwargs.get("shell")
        assert not suite.open_monitor("arbitrary")["ok"]
    finally:
        session.close()


def test_report_preserves_error_origin_scrubs_secrets_and_requires_review(workspace, monkeypatch):
    from test_launcher_gui import api

    session = Session("lanip", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    try:
        suite = SuiteApi()
        assert suite.record_activity(
            "Fallo password=privado 192.168.1.20",
            43,
            {"origin": "LANCTL.Scanner.Test", "code": "SCAN.TEST", "errorId": "0eTest"},
        )["ok"]
        monitor = api("lanmon")
        assert not monitor.open_report_form()["ok"]
        result = monitor.prepare_report(
            {"session": session.id, "description": "Error de escaneo", "includeActivity": True}
        )
        assert result["ok"], result
        assert result["report"]["errors"][0]["origin"] == "LANCTL.Scanner.Test"
        assert "privado" not in result["markdown"] and "192.168.1.20" not in result["markdown"]
        assert result["report"]["logs"][0]["source"] == "gui-activity"
        with patch("webbrowser.open", return_value=True) as browser:
            assert monitor.open_report_form()["opened"]
            assert browser.call_args.args[0].startswith(
                "https://github.com/CctrGy/LANCTL/issues/new?"
            )
        assert not api("lanrack").prepare_report({})["ok"]
    finally:
        session.close()


def test_update_rpc_returns_immediately_and_official_browser_is_explicit(workspace):
    from threading import Event

    release = {
        "status": "available",
        "available": "9.0.0",
        "installed": "0.3.4-alpha.1",
        "url": "https://github.com/CctrGy/LANCTL/releases/tag/v9.0.0",
        "notes": "Nueva versión",
    }
    started, finish = Event(), Event()

    def check(**kwargs):
        started.set()
        assert finish.wait(3)
        return release

    suite = SuiteApi()
    with (
        patch("lanctl.core.updates.UpdateService.check", side_effect=check),
        patch("webbrowser.open", return_value=True) as browser,
    ):
        assert suite.check_updates()["status"] == "checking"
        assert started.wait(1)
        assert suite.update_status()["status"] == "checking"
        assert not browser.called
        finish.set()
        import time

        for _ in range(100):
            if suite.update_status()["status"] != "checking":
                break
            time.sleep(0.01)
        assert suite.update_status()["available"] == "9.0.0"
        assert suite.open_update_release()["opened"]
        assert browser.call_args.args[0] == release["url"]


def test_auto_close_records_launch_before_destroying_window(workspace, monkeypatch):
    from unittest.mock import Mock

    from lanctl.core import config
    from lanctl.core.activity import ActivityStore

    config.save_config({**config.load_config(), "closeGuiOnLaunch": True})
    session = Session("lanctl", "gui", config.load_config())
    monkeypatch.setattr("lanctl.core.session._current", session)
    suite = SuiteApi()
    suite._desktop._window = Mock()

    def destroyed():
        assert any("LANWIRE" in row["message"] for row in ActivityStore().query(session=session.id))

    suite._desktop._window.destroy.side_effect = destroyed
    try:
        with (
            patch("lanctl.apps.suite.gui.subprocess.Popen"),
            patch("lanctl.core.gui_instance.focus_gui"),
        ):
            assert suite.launch_gui("lanwire")["closed"]
            suite._desktop._window.destroy.assert_called_once()
    finally:
        session.close()


def test_scan_selection_rejects_missing_origin_without_consuming_request(workspace, monkeypatch):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.core.first_scan import request_first_scan, scan_choices

    monkeypatch.setattr("lanctl.core.network_interfaces.ipv4_interfaces", list)
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop = DesktopApi()
    request_first_scan()
    with patch("lanctl.apps.ip.interfaces.cli.commands.list.run_list") as execute:
        result = desktop.scan_network("normal", "7:192.0.2.10", "192.0.2.0/24")
    assert not result["ok"]
    execute.assert_not_called()
    assert scan_choices()["requested"] is True


def test_first_scan_failure_can_retry_before_request_is_consumed(workspace, monkeypatch):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.core.first_scan import request_first_scan

    nic = {
        "id": "7:192.0.2.10",
        "name": "Ethernet de prueba",
        "index": 7,
        "address": "192.0.2.10",
        "prefixLength": 24,
        "network": "192.0.2.0/24",
    }
    monkeypatch.setattr("lanctl.core.network_interfaces.ipv4_interfaces", lambda: [nic])
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop = DesktopApi()
    request_first_scan()
    with patch("lanctl.apps.ip.interfaces.cli.commands.list.run_list", side_effect=[1, 0]) as scan:
        assert not desktop.scan_network("normal", nic["id"], nic["network"])["ok"]
        choices = desktop.first_scan_options()
        assert choices["requested"] is True
        assert choices["networks"] == [nic]
        assert desktop.scan_network("normal", nic["id"], nic["network"])["ok"]
        assert scan.call_count == 2
    assert desktop.first_scan_options()["requested"] is False


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_plugin_runtime_limits_are_visible_and_unavailable_actions_disabled(workspace, monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock

    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    session = Session("lanctl", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    suite = SuiteApi()
    manifest = SimpleNamespace(
        plugin_id="test.runtime",
        name="Plugin de prueba",
        description="Prueba de estado",
        version="1.0.0",
        author="Pruebas",
        minimum_lanctl="0.3.0",
        maximum_lanctl=None,
        capabilities=[],
        permissions=[],
        runtime="trusted",
    )
    plugin = SimpleNamespace(
        manifest=manifest,
        signature="",
        state=SimpleNamespace(value="DISABLED"),
        granted=set(),
        trusted=False,
        error="",
    )
    manager = Mock()
    manager.list.return_value = [plugin]
    manager.publishers.is_trusted.return_value = False
    status = {
        "schemaVersion": 1,
        "active": False,
        "coreAccess": False,
        "restartRequired": True,
        "cleanupPending": False,
        "execution": "legacy-in-process",
    }
    manager.runtime_status.return_value = status
    root = Path(__file__).resolve().parents[1]
    try:
        with (
            playwright() as p,
            patch("lanctl.apps.suite.gui.get_plugin_manager", return_value=manager),
            patch.object(
                suite,
                "_configuration_status",
                return_value={"hasSettings": False, "settingsError": ""},
            ),
            patch(
                "lanctl.core.updates.UpdateService.check",
                return_value={"status": "current", "installed": "0.3.4-alpha.1"},
            ),
        ):
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1100, "height": 780})
            page.expose_function("rpc", lambda method, args: getattr(suite, method)(*args))

            def open_plugins():
                page.goto((root / "gui/suite.html").as_uri())
                page.evaluate(
                    "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
                )
                page.locator('nav [data-page="plugins"]').click()

            open_plugins()
            assert page.locator('[data-plugin-toggle="test.runtime"]').is_disabled()
            assert (
                "hilos nativos no se consideran detenidos"
                in page.locator(".plugin-runtime-warning").inner_text()
            )
            status.update(restartRequired=False, cleanupPending=True, execution="isolated")
            manifest.runtime = "stdio"
            open_plugins()
            assert page.locator('[data-plugin-toggle="test.runtime"]').is_disabled()
            assert "limpieza" in page.locator(".plugin-runtime-warning").inner_text()
            status["cleanupPending"] = False
            page.wait_for_function("!document.querySelector('[data-plugin-toggle]').disabled")
            browser.close()
    finally:
        session.close()


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_theme_preview_cancel_save_and_cross_window_sync(workspace, monkeypatch):
    from test_launcher_gui import api

    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    session = Session("lanrack", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    rack = api("lanrack")
    root = Path(__file__).resolve().parents[1]
    try:
        with playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            pages = [browser.new_page(viewport={"width": 1100, "height": 780}) for _ in range(2)]
            errors = []
            for page in pages:
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.expose_function("rpc", lambda method, args: getattr(rack, method)(*args))
                page.goto((root / "gui/launcher.html").as_uri())
                page.evaluate(
                    "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
                )
                page.wait_for_function(
                    "document.documentElement.classList.contains('gui-preferences-active')"
                )
            page = pages[0]
            page.locator("#gui-appearance").click()
            page.locator('[data-theme="light"]').click()
            assert (
                page.evaluate("getComputedStyle(document.body).backgroundColor")
                == "rgb(242, 245, 248)"
            )
            page.locator('[data-preference="cancel"]').click()
            assert rack.gui_preferences()["preferences"]["theme"] == "graphite"
            page.locator("#gui-appearance").click()
            page.locator('[data-theme="violet"]').click()
            page.locator('.preferences-dialog [name="fontScale"]').select_option("1.2")
            page.locator('.preferences-dialog [type="submit"]').click()
            page.wait_for_function("!document.querySelector('.preferences-dialog').open")
            pages[1].wait_for_function(
                "getComputedStyle(document.documentElement).getPropertyValue('--color-background').trim()==='#191622'"
            )
            assert rack.gui_preferences()["preferences"]["fontScale"] == 1.2
            assert not errors
            browser.close()
    finally:
        session.close()


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_monitor_activity_filters_pause_report_and_native_browser(workspace, monkeypatch, tmp_path):
    from test_launcher_gui import api

    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    session = Session("lanctl", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    suite, monitor = SuiteApi(), api("lanmon")
    assert suite.record_activity("Operación completada")["ok"]
    assert suite.record_activity(
        "Fallo de prueba 10.0.0.1 password=privado",
        43,
        {"origin": "LANCTL.GUI.Test", "code": "GUI.TEST", "errorId": "0eTest"},
    )["ok"]
    root = Path(__file__).resolve().parents[1]
    try:
        with playwright() as p, patch("webbrowser.open", return_value=True) as open_browser:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1100, "height": 780})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.expose_function("rpc", lambda method, args: getattr(monitor, method)(*args))
            page.goto((root / "gui/launcher.html").as_uri())
            page.evaluate(
                "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
            )
            page.locator('[data-monitor-page="activity"]').click()
            page.wait_for_function(
                "document.querySelectorAll('#monitor-evidence article').length===2"
            )
            page.locator("#monitor-level").select_option("40")
            assert page.locator("#monitor-evidence article").count() == 1
            page.locator("#monitor-pause").click()
            assert suite.record_activity("Error mientras la vista está pausada", 43)["ok"]
            page.wait_for_timeout(1700)
            assert page.locator("#monitor-evidence article").count() == 1
            page.locator("#monitor-pause").click()
            page.wait_for_function(
                "document.querySelectorAll('#monitor-evidence article').length===2"
            )
            page.locator("#report-bug").click()
            page.locator('.report-dialog [name="description"]').fill("Problema del inventario")
            page.locator('.report-dialog [type="submit"]').click()
            page.locator(".report-preview").wait_for(state="visible")
            preview = page.locator(".report-preview").inner_text()
            assert "LANCTL.GUI.Test" in preview
            assert "privado" not in preview and "10.0.0.1" not in preview
            page.evaluate("""Object.defineProperty(navigator, 'clipboard', {
                configurable: true,
                value: {writeText: async text => { window.copiedReport = text; }}
            })""")
            page.locator('[data-report="copy"]').click()
            page.wait_for_function(
                "document.querySelector('.report-state').textContent.includes('copiado')"
            )
            assert page.evaluate("window.copiedReport") == preview
            assert not open_browser.called
            page.locator('[data-report="github"]').click()
            page.wait_for_function(
                "document.querySelector('.report-state').textContent.includes('Formulario abierto')"
            )
            assert open_browser.call_count == 1
            page.screenshot(path=str(tmp_path / "lanmon-report.png"))
            assert not errors, errors
            browser.close()
    finally:
        session.close()


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_rack_dimension_editor_and_cross_launcher_storage(workspace, monkeypatch):
    from test_launcher_gui import api

    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    session = Session("lanrack", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    rack, wire = api("lanrack"), api("lanwire")
    identifier = rack.rack_create(
        {"prefix": "RK", "name": "Nuevo rack", "units": 24, "widthInches": 19}
    )["id"]
    root = Path(__file__).resolve().parents[1]
    try:
        with playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1100, "height": 780})
            page.expose_function("rpc", lambda method, args: getattr(rack, method)(*args))
            page.goto((root / "gui/launcher.html").as_uri())
            page.evaluate(
                "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
            )
            page.get_by_role("button", name="Editar dimensiones", exact=True).click()
            page.locator('[name="units"]').fill("52")
            page.locator('[name="widthInches"]').select_option("23")
            page.locator("#submit").click()
            page.wait_for_function("!document.querySelector('#detail').open")
            record = next(r for r in wire.bootstrap()["records"] if r["id"] == identifier)
            assert record["data"]["units"] == 52
            assert record["data"]["rackDimensions"]["widthInches"] == 23
            assert rack.bootstrap()["records"][0]["widthInches"] == 23
            browser.close()
    finally:
        session.close()


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_suite_footer_responsive_links_and_explicit_update(workspace, monkeypatch):
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    session = Session("lanctl", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    suite = SuiteApi()
    root = Path(__file__).resolve().parents[1]
    release = {
        "status": "available",
        "installed": "0.3.4-alpha.1",
        "available": "9.0.0",
        "url": "https://github.com/CctrGy/LANCTL/releases/tag/v9.0.0",
        "notes": "Mejoras de prueba",
        "deferred": True,
    }
    try:
        with (
            playwright() as p,
            patch("lanctl.core.updates.UpdateService.check", return_value=release) as check,
            patch("webbrowser.open", return_value=True) as open_browser,
        ):
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 780, "height": 560})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.expose_function("rpc", lambda method, args: getattr(suite, method)(*args))
            page.goto((root / "gui/suite.html").as_uri())
            page.evaluate(
                "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
            )
            page.locator(".launch-card").first.wait_for()
            assert page.locator("#clock").count() == 0
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
            footer = page.locator("footer").bounding_box()
            assert footer["y"] + footer["height"] <= 561
            page.locator('[data-official-link="reference"]').click()
            page.wait_for_function("document.activeElement.dataset.officialLink==='reference'")
            assert open_browser.call_args.args[0] == "https://cctrgy.github.io/lanctl/reference/"
            page.locator('[data-page="settings"]').click()
            page.locator('[data-support="updates"]').click()
            page.wait_for_function(
                "document.querySelector('.update-state').textContent.includes('superior')"
            )
            assert check.call_args.kwargs["manual"] is True
            before = open_browser.call_count
            page.locator(".update-link").click()
            page.wait_for_function("document.activeElement.classList.contains('update-link')")
            assert open_browser.call_count == before + 1
            page.locator('[data-update="close"]').click()
            page.screenshot(path=str(root / "tmp/suite-pending-settings.png"))
            assert not errors, errors
            page.evaluate("""() => {
              const previous = window.pywebview.api;
              window.pywebview.api = new Proxy(previous,{get(target,key){
                if(key==='record_activity') return (...args)=>new Promise(resolve=>{
                  window.releaseRecord=()=>previous.record_activity(...args).then(resolve);
                });
                return target[key];
              }});
              message('Último mensaje antes del cierre');
              window.pendingClose=call('request_close').then(()=>{window.closeFinished=true;});
            }""")
            page.wait_for_timeout(100)
            assert not suite._desktop._closing
            page.evaluate("window.releaseRecord()")
            page.wait_for_function("window.closeFinished===true")
            assert suite._desktop._closing
            browser.close()
    finally:
        session.close()


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_first_scan_retries_and_preserves_selected_origin_and_range(workspace, monkeypatch):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.core.first_scan import request_first_scan

    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    session = Session("lanip", "gui", workspace)
    monkeypatch.setattr("lanctl.core.session._current", session)
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        desktop = DesktopApi()
    networks = []
    monkeypatch.setattr("lanctl.core.network_interfaces.ipv4_interfaces", lambda: list(networks))
    request_first_scan()
    root = Path(__file__).resolve().parents[1]
    payload = desktop.bootstrap()
    assert payload["ok"], payload
    try:
        with (
            playwright() as p,
            patch("lanctl.apps.ip.interfaces.cli.commands.list.run_list", return_value=0) as scan,
        ):
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(viewport={"width": 1100, "height": 780})
            page.expose_function("rpc", lambda method, args: getattr(desktop, method)(*args))
            page.goto((root / "gui/index.html").as_uri())
            page.evaluate(
                "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
            )
            page.locator(".first-scan-dialog").wait_for(state="visible")
            assert not scan.called
            assert page.locator('.first-scan-dialog [type="submit"]').is_disabled()
            assert desktop.first_scan_options()["requested"] is True
            networks.append(
                {
                    "id": "7:192.0.2.10",
                    "name": "Ethernet de prueba",
                    "index": 7,
                    "address": "192.0.2.10",
                    "prefixLength": 24,
                    "network": "192.0.2.0/24",
                }
            )
            page.locator('[data-first-scan="retry"]').click()
            page.locator('.first-scan-dialog option[value="7:192.0.2.10"]').wait_for(
                state="attached"
            )
            page.locator('.first-scan-dialog [name="range"]').fill("192.0.2.0/25")
            page.locator('.first-scan-dialog [type="submit"]').click()
            page.wait_for_function("!document.querySelector('.first-scan-dialog').open")
            page.wait_for_function("!document.body.classList.contains('busy')")
            assert scan.call_count == 1
            assert scan.call_args.args[0].interface == "7:192.0.2.10"
            assert scan.call_args.args[0].network == "192.0.2.0/25"
            assert desktop.first_scan_options()["requested"] is False
            page.locator("#scan-target").click()
            page.locator('.first-scan-dialog [name="source"]').select_option("")
            page.locator('.first-scan-dialog [type="submit"]').click()
            page.locator("#scan-network").click()
            page.wait_for_function("!document.body.classList.contains('busy')")
            assert scan.call_count == 2
            assert scan.call_args.args[0].interface is None
            browser.close()
    finally:
        session.close()


def test_projects_directory_persists_resolves_relative_and_preserves_project(
    workspace, tmp_path, monkeypatch
):
    from lanctl.core import config

    directory = tmp_path / "chosen"
    directory.mkdir()
    monkeypatch.chdir(tmp_path)
    suite = SuiteApi()
    result = suite.set_project_directory("chosen")
    assert result["ok"] and result["directory"] == str(directory)
    assert config.load_config()["projectsDirectory"] == str(directory)
    assert SuiteApi().project_defaults()["directory"] == str(directory)
    created = suite.create_project("Directory check")
    assert created["ok"], created
    project = config.load_config()["activeProject"]
    assert Path(project).parent == directory
    before = Path(project).read_bytes()
    restored = suite.set_project_directory(None)
    assert restored["ok"] and restored["configuredDirectory"] is None
    assert config.load_config()["activeProject"] == project
    assert Path(project).read_bytes() == before


def test_projects_directory_rejects_invalid_or_unwritable_without_saving(workspace, tmp_path):
    from lanctl.core import config

    suite = SuiteApi()
    before = config.CONFIG_PATH.read_bytes()
    file = tmp_path / "file"
    file.write_text("existing", encoding="utf-8")
    for value in ("", 42, str(file), str(tmp_path / "missing")):
        assert not suite.set_project_directory(value)["ok"]
        assert config.CONFIG_PATH.read_bytes() == before
    with patch("tempfile.TemporaryFile", side_effect=PermissionError("denied")):
        result = suite.set_project_directory(str(tmp_path))
    assert not result["ok"] and "denied" in result["error"]
    assert config.CONFIG_PATH.read_bytes() == before


def test_monitor_session_metadata_distinguishes_start_from_retained_record(workspace):
    from test_launcher_gui import api

    from lanctl.core.activity import ActivityStore
    from lanctl.core.coordination import Coordinator

    coordinator = Coordinator()
    identifier = coordinator.register("lanip", "gui")
    store = ActivityStore()
    try:
        first = store.append("First", launcher="lanip", session=identifier)
        store.append("Second", launcher="lanip", session=identifier)
        monitor = api("lanmon")
        result = monitor.monitor_activity()
        assert result["ok"], result
        assert result["sessions"] == [identifier]
        details = result["sessionDetails"][0]
        assert details["id"] == identifier
        assert details["firstRecord"] == first["created"]
        assert details["started"] <= details["firstRecord"]
        # More than 500 later events cannot turn the first displayed row into
        # a purported session start or first retained record.
        for _ in range(510):
            store.append("Later", launcher="lanip", session=identifier)
        refreshed = monitor.monitor_activity()
        assert len(refreshed["records"]) == 500
        assert refreshed["sessionDetails"][0]["firstRecord"] == first["created"]
        coordinator.close(identifier)
        historical = monitor.monitor_activity(identifier)["sessionDetails"][0]
        assert "started" not in historical
        assert historical["firstRecord"] == first["created"]
    finally:
        coordinator.close(identifier)
