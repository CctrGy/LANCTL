"""Native-page browser regressions for P96 and P101 (opt-in Chromium)."""

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
GUI = Path(__file__).resolve().parents[1] / "gui"


def test_terminal_keeps_scroll_selection_and_bounded_history():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 960, "height": 640})
        page.goto((GUI / "suite.html").as_uri())
        page.evaluate("""() => {
          state.page='terminal';render();
          window.outputText='';
          window.pywebview={api:{terminal_output:async()=>({ok:true,text:outputText,running:true})}};
          appendTerminalOutput($('#terminal-output'),'retained output line\\n'.repeat(700));
        }""")
        assert page.evaluate("terminalAtEnd($('#terminal-output'))")
        host = page.locator("#terminal-output")
        host.hover()
        page.mouse.wheel(0, -700)
        page.wait_for_function("!terminalAtEnd($('#terminal-output'))")
        host.focus()
        host.press("Home")
        host.press("ArrowDown")
        page.wait_for_timeout(300)  # Let keyboard/wheel scrolling finish.
        page.evaluate("""() => {
          const host=$('#terminal-output');host.scrollTop=8000;
          window.originalNode=host.firstChild;
          const range=document.createRange();range.setStart(originalNode,8000);range.setEnd(originalNode,8010);
          window.getSelection().removeAllRanges();window.getSelection().addRange(range);
          window.selectedText=window.getSelection().toString();
          window.selectionTop=range.getBoundingClientRect().top;
          window.oldTop=host.scrollTop;
        }""")
        page.evaluate("readTerminal()")
        assert page.evaluate("$('#terminal-output').firstChild===originalNode")
        assert page.evaluate("$('#terminal-output').scrollTop===oldTop")
        assert page.evaluate("getSelection().toString()===selectedText")
        page.evaluate("outputText='new output\\n'.repeat(20);readTerminal()")
        assert page.evaluate("$('#terminal-output').scrollTop===oldTop")
        assert page.evaluate("getSelection().toString()===selectedText")
        # Trim old lines while retaining the selected text and its visual position.
        page.evaluate("outputText='more output lines\\n'.repeat(500);readTerminal()")
        assert len(host.inner_text()) <= 20000
        assert page.evaluate("getSelection().toString()===selectedText")
        assert page.evaluate(
            "Math.abs(getSelection().getRangeAt(0).getBoundingClientRect().top-selectionTop)<2"
        )
        page.locator("#terminal-latest").click()
        assert page.evaluate("terminalAtEnd($('#terminal-output'))")
        page.evaluate("outputText='tail\\n';readTerminal()")
        assert page.evaluate("terminalAtEnd($('#terminal-output'))")
        browser.close()


def test_inventory_new_group_works_without_a_selected_device():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 1280, "height": 800})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((GUI / "index.html").as_uri())
        page.evaluate("""() => {
          window.groupCalls=[];
          window.pywebview={api:{
            create_group:async(...args)=>{groupCalls.push(args);return {ok:true,devices:[],groups:[],summary:{},message:'Grupo creado'};}
          }};
          desktopReady=true;state.devices=[];clearSelected();
        }""")
        assert page.locator(".topbar #new-group").count() == 0
        assert page.locator(".inspector #new-group").count() == 1
        assert page.locator("#new-group").is_enabled()
        page.locator("#new-group").focus()
        page.keyboard.press("Enter")
        page.locator('#desktop-fields input[name="name"]').fill("LAB")
        page.locator('#desktop-fields input[name="description"]').fill("Grupo de prueba")
        page.locator('#desktop-form button[type="submit"]').click()
        page.wait_for_function("groupCalls.length===1")
        assert page.evaluate("groupCalls[0]") == ["LAB", "Grupo de prueba"]
        for width, height in ((1280, 800), (960, 640), (760, 720), (390, 844)):
            page.set_viewport_size({"width": width, "height": height})
            button = page.locator("#new-group")
            button.scroll_into_view_if_needed()
            box = button.bounding_box()
            assert box["x"] >= 0 and box["x"] + box["width"] <= width + 1
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        page.evaluate("setBusy(true)")
        assert page.locator("#new-group").is_disabled()
        page.evaluate("setBusy(false);document.body.classList.add('remote-mode')")
        assert not page.locator("#new-group").is_visible()
        assert not errors
        browser.close()


def test_projects_directory_picker_cancel_save_restore_and_defaults(tmp_path, monkeypatch):
    from unittest.mock import patch

    from lanctl.apps.suite.gui import SuiteApi
    from lanctl.core import config

    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path / "data"))
    marker = tmp_path / "data/config/migration-v2.complete"
    marker.parent.mkdir(parents=True)
    marker.write_text("LANCTL-DATA-V2\n", encoding="utf-8")
    monkeypatch.setattr(config, "CONFIG_PATH", marker.parent / "config.json")
    config.save_config({**config.load_config(), "activeProject": None, "projectsDirectory": None})
    selected = tmp_path / "chosen"
    selected.mkdir()
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        api = SuiteApi()
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(viewport={"width": 960, "height": 640})
        page.expose_function("rpc", lambda method, args: getattr(api, method)(*args))
        page.goto((GUI / "suite.html").as_uri())
        page.evaluate("""() => {
          window.pywebview={api:new Proxy({}, {get:(_,method)=>(...args)=>rpc(method,args)})};
          state.page='projects';render();
        }""")
        page.locator('[data-action="project-directory"]').click()
        path = page.locator(".project-directory-path")
        initial = path.inner_text()
        with patch.object(api, "select_project_directory", return_value={"ok": True, "path": ""}):
            page.get_by_role(
                "button",
                name=page.evaluate("LanctlI18n.t('LANCTL.UI.TEXT.CHOOSE_FOLDER')"),
                exact=True,
            ).click()
            page.wait_for_function("!document.querySelector('#fields button').disabled")
        assert path.inner_text() == initial
        assert config.load_config()["projectsDirectory"] is None
        with patch.object(
            api, "select_project_directory", return_value={"ok": True, "path": str(selected)}
        ):
            page.get_by_role(
                "button",
                name=page.evaluate("LanctlI18n.t('LANCTL.UI.TEXT.CHOOSE_FOLDER')"),
                exact=True,
            ).click()
            page.wait_for_function(
                "value=>document.querySelector('.project-directory-path').textContent===value",
                arg=str(selected),
            )
        assert config.load_config()["projectsDirectory"] == str(selected)
        page.locator("#close-dialog").click()
        page.locator('[data-action="new-project"]').click()
        assert page.locator('[name="directory"]').input_value() == str(selected)
        page.locator("#close-dialog").click()
        page.locator('[data-action="project-directory"]').click()
        page.get_by_role(
            "button",
            name=page.evaluate('LanctlI18n.t("LANCTL.UI.VIEW.RESTORE_AUTOMATIC_LOCATION")'),
        ).click()
        page.wait_for_function(
            "value=>document.querySelector('.project-directory-path').textContent!==value",
            arg=str(selected),
        )
        assert config.load_config()["projectsDirectory"] is None
        browser.close()


def test_monitor_session_dates_ids_collision_and_selection():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page(
            viewport={"width": 1100, "height": 780}, timezone_id="Europe/Madrid"
        )
        page.goto((GUI / "launcher.html").as_uri())
        page.evaluate("""() => {
          window.evidence={ok:true,records:[{session:'historical',message:'Old event'}],
            sessions:['historical','abcdef001','abcdef002','no-date'],sessionDetails:[
              {id:'historical',firstRecord:1793000000},
              {id:'abcdef001',started:1793100000.1},{id:'abcdef002',started:1793100000.2}
            ]};
          window.calls=[];
          window.pywebview={api:{monitor_activity:async(...args)=>{calls.push(args);return evidence;}}};
          state={launcher:'lanmon'};
          window.openLanmonView('activity');
        }""")
        page.wait_for_function("document.querySelector('#monitor-session').options.length===5")
        options = page.locator("#monitor-session option").evaluate_all(
            "items=>items.map(o=>({value:o.value,label:o.textContent}))"
        )
        assert [item["value"] for item in options[1:]] == [
            "abcdef002",
            "abcdef001",
            "historical",
            "no-date",
        ]
        labels = {item["value"]: item["label"] for item in options}
        assert "Europe/Madrid" in labels["abcdef001"]
        assert "abcdef001" in labels["abcdef001"]  # shared prefix extends until unique
        assert (
            page.evaluate("LanctlI18n.t('LANCTL.UI.FRAGMENT.FIRST_RETAINED_RECORD')").strip(" ·")
            in labels["historical"]
        )
        assert (
            page.evaluate("LanctlI18n.t('LANCTL.UI.FRAGMENT.UNKNOWN_DATE')").strip(" ·")
            in labels["no-date"]
        )
        for width in (1100, 390):
            page.set_viewport_size({"width": width, "height": 780})
            bounds = page.locator("#monitor-session").bounding_box()
            assert bounds["x"] + bounds["width"] <= width + 1
        page.locator("#monitor-session").select_option("historical")
        page.wait_for_function("calls.some(args=>args[0]==='historical')")
        page.locator("#monitor-evidence details summary").click()
        assert page.locator("#monitor-evidence code").inner_text() == "historical"
        page.evaluate("window.openLanmonView('report')")
        select = page.locator('[name="reportSession"]')
        assert select.input_value() == "historical"
        assert select.locator('option[value="historical"]').inner_text() == labels["historical"]
        page.locator('[data-report="close"]').click()
        page.evaluate("evidence={...evidence,sessions:[],sessionDetails:[]}")
        page.wait_for_function("document.querySelector('#monitor-session').options.length===2")
        assert page.locator("#monitor-session").input_value() == "historical"
        browser.close()
