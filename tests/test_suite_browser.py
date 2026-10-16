"""Optional desktop layout regression checks with long project/plugin lists."""

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_suite_footer_stays_visible_when_lists_scroll():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.goto((Path(__file__).resolve().parents[1] / "gui/suite.html").as_uri())
        page.evaluate("""() => {
          state.projects=Array.from({length:50},(_,i)=>({name:'Proyecto '+i,path:'C:/Projects/'+i+'.vlf'}));
          state.plugins=Array.from({length:50},(_,i)=>({id:'demo.plugin'+i,name:'Plugin '+i,description:'Descripción del plugin',version:'1.2.3',author:'Autor de prueba',runtime:'isolated',state:'DISABLED'}));
        }""")
        for width, height in ((790, 570), (660, 460), (375, 650)):
            page.set_viewport_size({"width": width, "height": height})
            for section in ("projects", "plugins"):
                page.evaluate("section=>{state.page=section;render();}", section)
                assert page.locator(".collection-list").evaluate(
                    "el=>el.scrollHeight>el.clientHeight"
                )
                before = page.locator("footer").bounding_box()
                toolbar = page.locator(".toolbar").bounding_box()
                search = page.locator(".collection-search").bounding_box()
                for position in (0, 400, 100000):
                    page.locator(".collection-list").evaluate("(el,y)=>el.scrollTop=y", position)
                    after = page.locator("footer").bounding_box()
                    assert abs(before["y"] - after["y"]) < 1
                    assert after["y"] >= 0
                    assert after["y"] + after["height"] <= height + 1
                    assert page.locator("#external-cli").is_visible()
                    assert page.evaluate("window.scrollY") == 0
                    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    assert page.locator(".toolbar").bounding_box()["y"] == toolbar["y"]
                    assert page.locator(".collection-search").bounding_box()["y"] == search["y"]
                query = "Proyecto 49" if section == "projects" else "Plugin 49"
                page.locator("#collection-search").fill(query)
                assert page.locator(".collection-list .panel:visible").count() == 1
                if section == "plugins":
                    assert "1.2.3" in page.locator(".panel:visible .plugin-facts").inner_text()
                    assert (
                        "Autor de prueba"
                        in page.locator(".panel:visible .plugin-facts").inner_text()
                    )
                page.locator("#collection-search").fill("Sin resultados")
                assert page.locator(".collection-empty").is_visible()
                page.locator("#collection-search").fill("")
                assert page.locator(".collection-list .panel:visible").count() == 50
        browser.close()


def test_plugin_buttons_and_trust_dialog_follow_available_capabilities():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.goto((Path(__file__).resolve().parents[1] / "gui/suite.html").as_uri())
        page.evaluate("""() => {
          state.page='plugins';state.plugins=[
            {id:'none',name:'No settings',runtime:'trusted',signature:'UNSIGNED',permissions:[],granted:[]},
            {id:'settings',name:'Configurable',runtime:'isolated',hasSettings:true,permissions:[],granted:[]}
          ];render();
          window.pywebview={api:{plugin_settings:async()=>({ok:true,fields:[{name:'retries',type:'integer',default:3}],values:{retries:3}})}};
        }""")
        assert page.locator('[data-plugin-config="none"]').count() == 0
        page.locator('[data-plugin-config="settings"]').click()
        assert page.locator('[name="retries"]').input_value() == "3"
        page.locator("#close-dialog").click()
        page.locator('[data-plugin-toggle="none"]').click()
        assert "no tiene una firma válida" in page.locator("#fields").inner_text()
        assert not page.locator("#submit").is_visible()
        page.locator("#close-dialog").click()
        page.evaluate("state.plugins[0].signature='VALID_ED25519:abcdef';togglePlugin('none')")
        assert "abcdef" in page.locator("#fields").inner_text()
        assert page.get_by_text("Autorizar editor seleccionando su LCP firmado…").is_visible()
        assert not page.locator("#submit").is_visible()
        browser.close()


def test_project_edit_form_discard_confirmation_and_preserved_revision():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.goto((Path(__file__).resolve().parents[1] / "gui/suite.html").as_uri())
        page.evaluate("""() => {
          state.page='projects';state.projects=[{name:'Original',path:'example.vlf'}];render();
          window.saved=[];window.pywebview={api:{
            project_metadata:async()=>({ok:true,values:{name:'Original'},revision:'rev-1'}),
            save_project_metadata:async(...args)=>{window.saved.push(args);return {ok:true,message:'Guardado',projects:[{name:args[1].name,path:args[0]}]};}
          }};
        }""")
        page.locator('[data-edit-project="example.vlf"]').click()
        assert page.locator("#fields input").count() == 7
        page.locator('[name="name"]').fill("Renamed")
        page.locator("#dismiss").click()
        page.locator("#confirmation-cancel").click()
        assert page.locator("#dialog").is_visible()
        assert page.evaluate("saved.length") == 0
        page.evaluate("void suiteClose()")
        page.locator("#confirmation-cancel").click()
        assert page.locator("#dialog").is_visible()
        assert page.evaluate("saved.length") == 0
        page.locator("#submit").click()
        page.wait_for_function("saved.length===1 && !document.querySelector('#dialog').open")
        assert page.evaluate("saved[0][2]") == "rev-1"
        assert page.evaluate("saved[0][1].name") == "Renamed"
        assert page.locator(".panel h2").inner_text() == "Renamed"
        browser.close()


def test_home_terminal_and_project_defaults_fit_client_area():
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.goto((Path(__file__).resolve().parents[1] / "gui/suite.html").as_uri())
        page.evaluate("""() => {
          window.pywebview={api:{
            project_state:async()=>({ok:true,dirty:false}),
            project_defaults:async()=>({ok:true,directory:'C:/Projects',lan:'LAN principal'})
          }};
        }""")
        for width, height in ((790, 570), (660, 460), (1440, 900)):
            page.set_viewport_size({"width": width, "height": height})
            page.evaluate("state.page='home';render()")
            assert page.locator("#content").evaluate("e=>e.scrollHeight<=e.clientHeight+1")
            assert page.locator("[data-launcher-settings]").count() == 5
            page.evaluate("state.page='terminal';render()")
            page.locator("#terminal-output").evaluate("e=>e.textContent='line\\n'.repeat(500)")
            assert page.locator("#content").evaluate("e=>e.scrollHeight<=e.clientHeight+1")
            assert page.locator("#command").is_visible()
            assert page.locator("#terminal-output").evaluate("e=>e.scrollHeight>e.clientHeight")
        page.evaluate("void newProject()")
        assert page.locator('[name="directory"]').input_value() == "C:/Projects"
        assert page.locator('[name="directory"]').is_editable()
        assert page.locator('[name="lan"]').input_value() == "LAN principal"
        browser.close()
