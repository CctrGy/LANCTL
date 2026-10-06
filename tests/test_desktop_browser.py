"""Optional browser checks: LANCTL_GUI_BROWSER_TESTS=1 pytest tests/test_desktop_browser.py."""

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_desktop_browser_flows(tmp_path):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((Path(__file__).resolve().parents[1] / "gui/index.html").as_uri())
        page.evaluate("""() => {
          const device = {id:'test-1',ip:'192.0.2.1',mac:'02:00:00:00:00:01',alias:'ROUTER',
            name:'Router de prueba',description:'Red de demostración',manufacturer:'Example',
            groups:['LAB'],protocols:['https'],cnf:'O',active:true,responseMs:2,iconId:'',lastSeen:''};
          const inventory = {ok:true,devices:[device],summary:{total:1,active:1},editHistory:{}};
          window.pywebview = {api:{
            bootstrap:async()=>({...inventory,theme:{},projects:[],icons:[],version:'test'}),
            project_state:async()=>({ok:true,dirty:false}),
            list_devices:async()=>inventory,
            get_settings:async()=>({ok:true,fields:[{key:'workers',label:'Workers',value:64}]}),
            save_settings:async()=>({ok:true,message:'Configuración guardada correctamente'}),
            save_project:async()=>({...inventory,projects:[],message:'Proyecto guardado correctamente'}),
            create_project:async()=>({...inventory,devices:[],projects:[],message:'Proyecto vacío creado'}),
          }};
          window.dispatchEvent(new Event('pywebviewready'));
        }""")
        page.get_by_role("cell", name="ROUTER", exact=True).wait_for()
        page.locator("#state-filter").select_option("inactive")
        assert page.locator("#device-rows tr").count() == 0
        page.locator("#state-filter").select_option("all")
        assert page.locator("#device-rows tr").count() == 1
        page.locator("#desktop-settings").click()
        page.locator("input[name=workers]").fill("32")
        page.locator("#desktop-form button[type=submit]").click()
        page.get_by_text("Configuración guardada correctamente", exact=True).first.wait_for()
        page.keyboard.press("Control+s")
        page.get_by_text("Proyecto guardado correctamente", exact=True).first.wait_for()
        page.get_by_role("cell", name="ROUTER", exact=True).click()
        page.locator("#edit-name").fill("Edición sin aplicar")
        page.evaluate("window.desktopDataChanged=true")
        page.wait_for_timeout(1200)
        assert page.locator("#edit-name").input_value() == "Edición sin aplicar"
        assert page.evaluate("window.desktopDataChanged") is True
        page.locator("#edit-name").fill("Router de prueba")
        page.wait_for_function("window.desktopDataChanged === false")
        page.screenshot(path=str(tmp_path / "lanip-desktop.png"), full_page=True)
        page.locator("#project-new").click()
        page.locator("input[name=name]").fill("Prueba")
        page.locator("#desktop-form button[type=submit]").click()
        page.get_by_text("Proyecto vacío creado", exact=True).first.wait_for()
        assert page.locator("#device-rows tr").count() == 0
        page.set_viewport_size({"width": 960, "height": 640})
        assert page.locator("#desktop-settings").is_visible()
        assert not errors
        browser.close()
