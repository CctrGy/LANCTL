"""Optional browser checks for the production launcher views."""

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)


def test_real_launcher_views_and_action_arguments(tmp_path):
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    root = Path(__file__).resolve().parents[1]
    payloads = {
        "lanwire": {
            "records": [
                {
                    "id": "SW001",
                    "prefix": "SW",
                    "revision": "rev1",
                    "data": {
                        "type": "device.switch",
                        "name": "Switch principal",
                        "ports": {"X1": {"kind": "wire.copper"}},
                    },
                },
                {
                    "id": "WL001",
                    "prefix": "WL",
                    "revision": "rev2",
                    "data": {
                        "type": "wire",
                        "kind": "wire.copper",
                        "name": "Enlace",
                        "endpoints": [],
                    },
                },
            ]
        },
        "lanrack": {
            "records": [
                {
                    "id": "RK001",
                    "name": "Rack real",
                    "units": 24,
                    "location": {},
                    "occupants": [
                        {"id": "SW001", "name": "Switch", "unit": 18, "type": "device.switch"}
                    ],
                }
            ]
        },
        "lanaccess": {
            "locked": False,
            "portable": False,
            "devices": [{"id": "dev1", "name": "Router", "protocols": ["ssh"]}],
            "records": [
                {
                    "credentialId": "cred1",
                    "deviceId": "dev1",
                    "element": "Router",
                    "protocol": "ssh",
                    "username": "operador",
                    "revision": "credential-revision",
                }
            ],
        },
        "lanmon": {
            "records": [
                {
                    "id": "dev1",
                    "name": "Router",
                    "ip": "192.0.2.1",
                    "presence": "online",
                    "health": "healthy",
                    "latency": 2.3,
                }
            ],
            "incidents": [],
            "session": None,
            "process": {"running": False},
        },
    }
    with sync_playwright() as p:
        b = p.chromium.launch(channel="msedge", headless=True)
        page = b.new_page(viewport={"width": 1100, "height": 780})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        for app, payload in payloads.items():
            page.goto((root / "gui/launcher.html").as_uri())
            page.evaluate(
                """payload => {
                  window.calls = [];
                  window.pywebview = {api: {
                    bootstrap: async () => payload,
                    monitor_samples: async () => ({ok:true, samples:[]}),
                    monitor_device: async identifier => {
                      calls.push(['monitor_device', identifier]);
                      const row = payload.records.find(record => record.id === identifier);
                      return {ok:true, device: {
                        id:row.id, revision:'device-revision',
                        editable:{name:row.name, alias:'', description:'', ip:row.ip},
                        groups:[], groupCatalog:[{name:'BASIC', editable:false}]
                      }};
                    },
                    settings: async () => ({ok:true, entries:[], categories:{}}),
                    wire_create: async (...args) => {
                      calls.push(['wire_create', ...args]);
                      return {ok:true, id:'WL002'};
                    }
                  }};
                  window.dispatchEvent(new Event('pywebviewready'));
                }""",
                {
                    "ok": True,
                    "launcher": app,
                    "project": "C:/Office.vlf",
                    "projectName": "Oficina",
                    "version": "0.3.3",
                    "storage": "C:/test/storage",
                    **payload,
                },
            )
            page.locator("#brand span").wait_for()
            assert page.locator("#brand").inner_text().startswith(app.upper())
            page.screenshot(path=str(tmp_path / f"{app}-gui.png"))
            if app != "lanrack":
                page.locator('[data-action="details"]').click()
                assert page.locator("#detail").is_visible()
                if app == "lanmon":
                    page.locator('[name="name"]').wait_for()
                    assert page.locator('[name="name"]').input_value() == "Router"
                    assert page.locator('[name="ip"]').input_value() == "192.0.2.1"
                    assert page.evaluate("calls") == [["monitor_device", "dev1"]]
                    assert page.locator(".support-dialog[open]").count() == 0
                page.locator("#cancel").click()
                page.locator("#search").fill("no-existe")
                assert "No hay coincidencias" in page.locator("#canvas").inner_text()
                page.locator("#search").fill("")
            if app == "lanwire":
                page.locator('[data-action="new"]').click()
                page.locator('[name="kind"]').select_option("wire.copper")
                page.locator('[name="prefix"]').fill("WL")
                page.locator('[name="name"]').fill("Nuevo enlace")
                page.locator("#submit").click()
                page.wait_for_function("calls.length===1")
                assert page.evaluate("calls[0][1].name") == "Nuevo enlace"
            page.set_viewport_size({"width": 780, "height": 560})
            assert page.locator("footer").bounding_box()["y"] < 560
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth"), app
            page.set_viewport_size({"width": 1100, "height": 780})
        assert not errors, errors
        b.close()
        print(
            "4 GUI: renderizado, búsqueda, detalles, edición, viewport y ausencia de errores JS verificados."
        )
