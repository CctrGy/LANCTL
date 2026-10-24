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
            device_record:async()=>({ok:true,device,record:{...device,previousIPs:['192.0.2.20'],discoveryMethods:['ARP']}}),
            get_device_details:async()=>({ok:true,device,diagnostic:{open_ports:[{port:443,service:'https',label:'HTTPS',interactive:true,evidence:'TLS'}]}}),
            open_service:async(...args)=>{window.lastService=args;return {ok:true,message:'Acceso directo'};},
            scan_network:async()=>({...inventory,message:'Escaneo terminado'}),
            scan_status:async()=>({ok:true,current:1,total:1}),
                create_group:async(name,description)=>{window.lastGroup={name,description};return {...inventory,groupCatalog:[{name:name.toUpperCase(),description}],message:'Grupo creado'};},
                open_cli:async()=>{window.lanipCliOpened=true;return {ok:true,message:'CLI de LANIP abierto'};},
                open_suite:async()=>{window.suiteGuiOpened=true;return {ok:true,message:'LANCTL abierto'};},
                group_action:async(action,name)=>{if(action==='add')device.groups=[...new Set([...device.groups,name])];else device.groups=device.groups.filter(n=>n!==name);window.lastGroupAction={action,name};return inventory;},
                update_device:async(id,values)=>{window.lastUpdate={id,values};Object.assign(device,values);return {...inventory,message:'Elemento actualizado'};},
            get_settings:async()=>({ok:true,fields:[{key:'workers',label:'Workers',value:64}]}),
            save_settings:async()=>({ok:true,message:'Configuración guardada correctamente'}),
            save_project:async()=>({...inventory,projects:[],message:'Proyecto guardado correctamente'}),
            create_project:async()=>({...inventory,devices:[],projects:[],message:'Proyecto vacío creado'}),
          }};
          window.dispatchEvent(new Event('pywebviewready'));
        }""")
        page.get_by_role("cell", name="ROUTER", exact=True).wait_for()
        assert page.locator(".main-navigation").is_hidden()
        assert page.locator("#open-terminal").is_disabled()
        assert page.locator("#show-shares").is_disabled()
        assert page.locator("#open-device").is_enabled()
        page.locator("#lanctl-gui").click()
        page.wait_for_function("window.suiteGuiOpened")
        page.locator("#new-group").click()
        page.locator('input[name="name"]').fill("nuevo")
        page.locator('input[name="description"]').fill("Grupo de prueba")
        page.locator('#desktop-form button[type="submit"]').click()
        page.wait_for_function("window.lastGroup?.name === 'nuevo'")
        assert page.evaluate("window.lastGroup.description") == "Grupo de prueba"
        assert page.locator('#group-filter option[value="NUEVO"]').count() == 1
        page.locator("#lanip-cli").click()
        page.wait_for_function("window.lanipCliOpened")
        page.locator("#advanced-filters summary").click()
        page.locator("#vendor-filter").select_option("Example")
        page.locator("#protocol-filter").select_option("https")
        assert page.locator("#device-rows tr").count() == 1
        page.locator("#cnf-filter").select_option("X")
        assert page.locator("#device-rows tr").count() == 0
        page.locator("#clear-filters").click()
        assert page.locator("#device-rows tr").count() == 1
        page.locator("#advanced-filters summary").click()
        assert page.locator('th[data-column="mac"]').is_hidden()
        page.locator("#inventory-view").select_option("complete")
        assert page.locator('th[data-column="mac"]').is_visible()
        page.locator("#inventory-view").select_option("essential")
        page.keyboard.press("Control+k")
        assert page.locator("#device-search").evaluate("el => el === document.activeElement")
        page.locator("#device-search").fill("does-not-exist")
        assert page.locator("#device-rows tr").count() == 0
        assert page.locator("#save-device").is_disabled()
        page.locator("#device-search").fill("")
        assert page.locator("#save-device").is_enabled()
        page.evaluate("applyTheme({id:'custom.palette',tokens:{'--color-accent':'#e0a0ff'}})")
        assert (
            page.evaluate("document.documentElement.style.getPropertyValue('--color-accent')")
            == "#e0a0ff"
        )
        page.evaluate(
            "applyTheme({id:'lanctl.theme.default.palette',tokens:{'--color-accent':'#25a9e8'}})"
        )
        assert (
            page.evaluate("document.documentElement.style.getPropertyValue('--color-accent')")
            == "#b2ef26"
        )
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
        page.get_by_role("cell", name="ROUTER", exact=True).dblclick()
        page.locator("#details-fields").get_by_text("Router de prueba", exact=True).wait_for()
        page.locator("#tab-record").click()
        assert "192.0.2.20" in page.locator("#sheet-record").inner_text()
        page.locator("#tab-ports").click()
        page.locator("#sheet-inspect").click()
        page.locator("#details-services button").click()
        assert page.evaluate("window.lastService") == ["test-1", "https", 443]
        page.locator("#tab-edit").click()
        assert page.locator("#edit-description").evaluate("el=>el.tagName") == "TEXTAREA"
        assert page.locator("#edit-description").get_attribute("maxlength") is None
        page.locator("#edit-name").fill("Nombre editado")
        page.locator("#save-device").click()
        page.get_by_text("Cambios guardados.", exact=True).wait_for()
        assert page.evaluate("window.lastUpdate.values.name") == "Nombre editado"
        assert page.evaluate("window.lastUpdate.values.ip") == "192.0.2.1"
        page.locator("#edit-name").fill("Router de prueba")
        page.locator("#save-device").click()
        page.wait_for_function("window.lastUpdate.values.name === 'Router de prueba'")
        page.locator("#tab-groups").click()
        page.locator("#sheet-new-group-name").fill("INLINE")
        page.locator("#sheet-new-group-description").fill("Creado en la ficha")
        page.locator("#sheet-create-group").click()
        page.wait_for_function("window.lastGroupAction?.name === 'INLINE'")
        assert page.locator("dialog[open]").count() == 1
        page.locator("#tab-edit").click()
        page.locator("#edit-name").fill("Edición sin aplicar")
        page.evaluate("window.desktopDataChanged=true")
        page.wait_for_timeout(1200)
        assert page.locator("#edit-name").input_value() == "Edición sin aplicar"
        assert page.evaluate("window.desktopDataChanged") is True
        page.locator("#edit-name").fill("Router de prueba")
        page.locator("#close-details").click()
        page.wait_for_function("window.desktopDataChanged === false")
        page.on("dialog", lambda dialog: pytest.fail("El escaneo no debe pedir confirmación"))
        page.locator("#scan-network").click()
        page.get_by_text("Escaneo terminado", exact=True).first.wait_for()
        assert (
            page.locator("#open-terminal").bounding_box()["y"]
            > page.locator(".table-panel").bounding_box()["y"]
        )
        page.screenshot(path=str(tmp_path / "lanip-desktop.png"), full_page=True)
        for selector in ("#project-new", "#project-open", "#project-select"):
            assert not page.locator(selector).is_visible()
        assert page.locator("#lanctl-gui").is_visible()
        page.set_viewport_size({"width": 960, "height": 640})
        assert page.locator("#desktop-settings").is_visible()
        for width, height in ((1280, 800), (960, 640), (760, 720), (390, 844)):
            page.set_viewport_size({"width": width, "height": height})
            assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.evaluate("""() => {
            window.pywebview.api.project_state = async () => ({ok:true, dirty:true, shared:true});
            window.pywebview.api.request_close = async decision => {
                window.closeDecision = decision; return {ok:true, closed:true};
            };
            void desktopClose();
        }""")
        page.locator("#save-dialog").wait_for()
        assert "otras sesiones" in page.locator("#save-dialog p").inner_text()
        page.get_by_role("button", name="Cerrar sin guardar", exact=True).click()
        page.wait_for_function("window.closeDecision === 'discard'")
        assert not errors
        browser.close()
