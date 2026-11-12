"""P134 rendering regression and optional P135 vector design review sheet."""

import os
from pathlib import Path

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_patch_panel_is_passive_and_skin_review(workspace):
    wire, rack = api("lanwire"), api("lanrack")
    switch = wire.wire_create({"kind": "switch.24ports", "prefix": "SW", "name": "Switch 24 RJ45"})[
        "id"
    ]
    panel = wire.wire_create({"kind": "panel", "prefix": "PN", "name": "Patch panel 24 RJ45"})["id"]
    original = wire.bootstrap()["records"]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, rack)
        page.wait_for_function("state.elements?.length >= 2")
        faces = page.evaluate(
            """([switchId,panelId]) => {
          const records = physicalInventory();
          const front = id => rackFace(records.find(r=>r.id===id));
          const optical = {id:'SW-SFP', data:{type:'device.switch', ports:Object.fromEntries(Array.from({length:48},(_,i)=>['S'+i,{kind:'wire.fiber'}]))}};
          return {switch:front(switchId),panel:front(panelId),optical:rackFace(optical),blank:rackFace({id:'ACCESSORY',data:{}},{kind:'blank',units:1,rackmount:true,rj45:0,sfp:0})};
        }""",
            [switch, panel],
        )
        assert "skin-panel-module" in faces["panel"]
        assert "skin-power" not in faces["panel"]
        assert faces["panel"].count('class="skin-panel-module"') == 24
        assert faces["switch"].count('data-connector="rj45"') == 24
        assert "skin-power" in faces["switch"]
        assert faces["optical"].count('data-connector="sfp"') == 48
        assert 'class="skin-vent"' not in faces["blank"]
        mixed = page.evaluate("""() => {
          const profiles = [5,8,16,24,48].flatMap(rj45 => [2,4,6].map(sfp=>({rj45,sfp})));
          profiles.push({rj45:48,sfp:8},{rj45:50,sfp:2});
          return profiles.map(({rj45,sfp}) => {
            const ports = Object.fromEntries([...Array.from({length:rj45},(_,i)=>['X'+i,{kind:'wire.copper'}]),...Array.from({length:sfp},(_,i)=>['S'+i,{kind:'wire.fiber'}])]);
            const svg = rackFace({id:`SW-${rj45}-${sfp}`,name:`Switch ${rj45} RJ45 + ${sfp} SFP`,data:{type:'device.switch',ports}});
            const element = document.createElement('div'); element.innerHTML=svg;
            const copper=[...element.querySelectorAll('[data-connector="rj45"] rect')];
            const fiber=[...element.querySelectorAll('[data-connector="sfp"] rect')];
            const x = r=>Number(r.getAttribute('x')), right=r=>x(r)+Number(r.getAttribute('width'));
            return {rj45,sfp,svg,copper:copper.length,fiber:fiber.length,left:Math.min(...copper.map(x)),copperRight:Math.max(...copper.map(right)),fiberLeft:Math.min(...fiber.map(x)),right:Math.max(...fiber.map(right))};
          });
        }""")
        for profile in mixed:
            assert profile["copper"] == profile["rj45"]
            assert profile["fiber"] == profile["sfp"]
            assert 440 <= profile["left"] < profile["copperRight"] < profile["fiberLeft"]
            assert profile["right"] <= 1160
        assert wire.bootstrap()["records"] == original
        output = os.environ.get("LANCTL_VISUAL_REVIEW_DIR")
        if output:
            destination = Path(output)
            destination.mkdir(parents=True, exist_ok=True)
            root = Path(__file__).resolve().parents[1]
            cards = [
                ("Switch · 24 RJ45", faces["switch"]),
                ("Patch panel pasivo · 24 RJ45", faces["panel"]),
                ("Switch óptico · 48 SFP", faces["optical"]),
            ]
            cards += [
                (f"Switch · {p['rj45']} RJ45 + {p['sfp']} SFP", p["svg"])
                for p in mixed
                if p["rj45"] in (24, 48) or (p["rj45"], p["sfp"]) == (8, 2)
            ]
            accessories = page.evaluate("""() => ['cable-comb','organizer','ventilation'].map(kind => ({
              kind, svg:rackFace({id:'AC-01',data:{type:'rack.'+kind,ports:{}}})
            }))""")
            for accessory in accessories:
                assert f"skin-{accessory['kind']}" in accessory["svg"]
                assert "data-connector=" not in accessory["svg"]
            cards += [(accessory["kind"], accessory["svg"]) for accessory in accessories]
            cards += [("Tapa ciega", faces["blank"])]
            css = (root / "gui/launcher.css").read_text()
            html = (
                '<!doctype html><html lang="es"><meta charset="utf-8"><title>Revisión P134 / P135</title><style>'
                + css
                + "body{margin:0;padding:30px;background:#11171a;color:#e1e9e4;font:15px sans-serif}main{max-width:1200px;margin:auto}h1{font-size:23px}p{color:#a5b4aa}article{margin:18px 0;padding:16px;border:1px solid #45554a;border-radius:9px;background:#1b2528}h2{font-size:14px;font-weight:500;margin:0 0 12px}.rack-face{height:auto;width:100%}</style><main><h1>P134 / P135 · Revisión de frentes</h1><p>Frentes reales de equipos y accesorios integrados en LANRACK. El prefijo común de P135 sigue pendiente.</p>"
                + "".join(
                    "<article><h2>" + label + "</h2>" + svg + "</article>" for label, svg in cards
                )
                + "</main></html>"
            )
            report = destination / "revision.html"
            report.write_text(html)
            page.goto(report.as_uri())
            for width in (1440, 980):
                page.set_viewport_size({"width": width, "height": 1100})
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                page.screenshot(path=str(destination / f"revision-{width}.png"), full_page=True)
        browser.close()


def test_tall_rack_fronts_do_not_shrink_to_viewport_height(workspace):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 52})["id"]
    wire.wire_create({"kind": "switch.24ports", "prefix": "SW", "rack": cabinet, "unit": 52})
    before = wire._service.database.path.read_bytes()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, rack)
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        page.evaluate("rackSkinsVisible=true;render()")

        def measure(width, height):
            page.set_viewport_size({"width": width, "height": height})
            page.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            return page.evaluate(
                """() => ({unit:parseFloat(getComputedStyle(document.querySelector('.rack-elevation')).getPropertyValue('--rack-unit-height')),width:document.querySelector('.rack-elevation').getBoundingClientRect().width,canvas:document.querySelector('#canvas').clientWidth,scroll:document.querySelector('#canvas').scrollHeight,height:document.querySelector('#canvas').clientHeight,ratio:(()=>{const m=document.querySelector('.rack-face').getScreenCTM();return {a:m.a,d:m.d}})()})"""
            )

        tall = measure(1440, 1000)
        short = measure(1440, 650)
        assert tall["unit"] == short["unit"] and short["unit"] >= 52
        assert short["scroll"] > short["height"]
        assert short["width"] > 1000
        narrow = measure(850, 700)
        assert narrow["unit"] >= 52 and narrow["width"] <= narrow["canvas"]
        assert abs(narrow["ratio"]["a"] - narrow["ratio"]["d"]) < 0.001
        assert wire._service.database.path.read_bytes() == before
        output = os.environ.get("LANCTL_VISUAL_REVIEW_DIR")
        if output:
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
            page.screenshot(path=str(Path(output) / "rack-readable.png"))
        browser.close()


def test_dark_tray_contains_small_device_fronts(workspace):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 8})["id"]
    tray = wire.wire_create(
        {
            "kind": "tray",
            "prefix": "TR",
            "name": "Bandeja de equipos",
            "rack": cabinet,
            "unit": 6,
            "heightU": 2,
        }
    )["id"]
    children = []
    for kind, prefix, name in (
        ("router.gateway", "RT", "Router"),
        ("router.otg", "OT", "OTG"),
        ("switch.5ports", "SW", "Switch 5 RJ45"),
    ):
        result = wire.wire_create({"kind": kind, "prefix": prefix, "name": name, "tray": tray})
        assert result["ok"], result
        children.append(result["id"])
    before = wire._service.database.path.read_bytes()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, rack)
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        page.evaluate("rackSkinsVisible=true;render()")
        front = page.locator(f'[data-rack-occupant="{tray}"]')
        assert front.locator(".skin-tray-chassis").count() == 1
        assert front.locator(".skin-vent").count() == 0
        for identifier in children:
            assert front.locator(f'[data-tray-device="{identifier}"]').count() == 1
            assert (
                front.locator(f'[data-tray-device="{identifier}"] title')
                .first.text_content()
                .find(identifier)
                >= 0
            )
        assert front.locator(".skin-small-switch .skin-small-port").count() == 5
        assert page.locator(".rack-elevation > button").count() == 7
        assert (
            front.locator(".skin-tray-chassis").evaluate("e=>getComputedStyle(e).fill")
            == "rgb(16, 23, 25)"
        )
        assert wire._service.database.path.read_bytes() == before
        output = os.environ.get("LANCTL_VISUAL_REVIEW_DIR")
        if output:
            page.screenshot(path=str(Path(output) / "tray-small-devices.png"))
        browser.close()
