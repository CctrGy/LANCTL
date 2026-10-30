"""Language rendering must leave inputs, technical output and data untouched."""

import os
from pathlib import Path

import pytest

from lanctl.shared.i18n import ENGLISH_STRINGS, SPANISH_STRINGS

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "filename", ["suite.html", "index.html", "launcher.html", "remote-setup.html"]
)
def test_real_pages_explicit_language_bindings_preserve_data(filename):
    playwright = pytest.importorskip("playwright.sync_api")
    with playwright.sync_playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto((ROOT / "gui" / filename).as_uri())
        page.evaluate("""() => {
          const host=document.createElement('div'); host.id='p100-fixture';
          host.innerHTML='<label id="p100-label"></label><pre id="p100-log">Guardar {raw} 127.0.0.1</pre><span id="p100-data">Sin proyecto</span>';
          document.body.append(host);
          LanctlI18n.bindText(host.querySelector('label'),'LANCTL.UI.TEXT.IP_ADDRESS');
          const input=document.createElement('input');input.value='Nombre del usuario';input.id='p100-input';host.querySelector('label').append(input);
          LanctlI18n.bindAttribute(input,'placeholder','LANCTL.UI.TEXT.IP_ADDRESS');
          const counter=document.createElement('span');counter.id='p100-count';host.append(counter);
          LanctlI18n.bindText(counter,'LANCTL.CLI.ELEMENT.LABEL',{value:'router <original>'});
          const empty=document.createElement('span');empty.id='p100-empty';host.append(empty);
          LanctlI18n.bindText(empty,'LANCTL.CLI.ELEMENT.LABEL',{value:''});
        }""")
        for code, strings in (("en", ENGLISH_STRINGS), ("es", SPANISH_STRINGS)):
            page.evaluate(
                "payload => LanctlI18n.setCatalog(payload)", {"code": code, "strings": strings}
            )
            assert page.locator("html").get_attribute("lang") == code
            assert (
                page.locator("#p100-label").evaluate("e=>e.firstChild.data")
                == strings["LANCTL.UI.TEXT.IP_ADDRESS"]
            )
            assert page.locator("#p100-input").input_value() == "Nombre del usuario"
            assert page.locator("#p100-count").inner_text() == strings[
                "LANCTL.CLI.ELEMENT.LABEL"
            ].format(value="router <original>")
            assert page.locator("#p100-empty").text_content() == strings[
                "LANCTL.CLI.ELEMENT.LABEL"
            ].format(value="")
            assert (
                page.locator("#p100-input").get_attribute("placeholder")
                == strings["LANCTL.UI.TEXT.IP_ADDRESS"]
            )
            assert page.locator("#p100-log").inner_text() == "Guardar {raw} 127.0.0.1"
            assert page.locator("#p100-data").inner_text() == "Sin proyecto"
            for key, value in page.locator("[data-i18n]").evaluate_all(
                "nodes=>nodes.filter(n=>n.isConnected).map(n=>[n.dataset.i18n,n.textContent])"
            ):
                assert value == strings[key]
        page.evaluate("""() => {
          const node=document.createElement('span');node.id='p100-dynamic';
          node.dataset.i18n='LANCTL.UI.TEXT.SAVE';document.body.append(node);
        }""")
        page.wait_for_function("document.querySelector('#p100-dynamic').textContent==='Guardar'")
        page.evaluate("""() => {
          const key='LANCTL.UI.TEXT.SAVE';
          const attack='<img src=x onerror="window.p100Injected=true">';
          LanctlI18n.setCatalog({code:'es',strings:{[key]:attack}});
          const host=document.createElement('div');host.id='p100-safe';
          host.innerHTML=LanctlI18n.html(key);document.body.append(host);
          if(typeof button==='function' && location.pathname.endsWith('launcher.html')) {
            const buttons=document.createElement('div');buttons.id='p100-safe-button';
            buttons.innerHTML=button(LanctlI18n.t(key),'test');document.body.append(buttons);
          }
        }""")
        assert page.locator("#p100-safe img").count() == 0
        assert page.locator("#p100-safe-button img").count() == 0
        assert page.evaluate("window.p100Injected === undefined")
        assert not errors
        browser.close()
