"""Regresiones del inventario CPD compartido y de su navegación gráfica."""

import json
import os
from pathlib import Path

import pytest
from test_launcher_gui import api

pytest_plugins = ["test_launcher_gui"]


def seed():
    wire, rack = api("lanwire"), api("lanrack")
    racks, switches = [], []
    for i, name in enumerate("ABCDEFG"):
        racks.append(
            wire.wire_create({"kind": "rack", "prefix": "RK", "name": "Rack " + name, "units": 48})[
                "id"
            ]
        )
        switches.append(
            wire.wire_create(
                {
                    "kind": "switch.48ports" if i == 0 else "switch.5ports",
                    "prefix": "SW",
                    "name": "Switch " + name,
                }
            )["id"]
        )
        row = next(r for r in wire.bootstrap()["records"] if r["id"] == switches[-1])
        assert wire.wire_update(row["id"], row["revision"], {"rack": racks[-1], "unit": 10})["ok"]
    cables = []
    # Ciclo y enlaces paralelos: no es un árbol.
    for i in range(7):
        cable = wire.wire_create(
            {"kind": "wire.copper", "prefix": "WL", "name": "Interconexión de sala " + str(i)}
        )["id"]
        row = next(r for r in wire.bootstrap()["records"] if r["id"] == cable)
        assert wire.wire_connect(
            cable,
            row["revision"],
            [
                {"device": switches[i], "port": "X1"},
                {"device": switches[(i + 1) % 7], "port": "X2"},
            ],
        )["ok"]
        cables.append(cable)
    cable = wire.wire_create({"kind": "wire.copper", "prefix": "WL", "name": "Redundancia A B"})[
        "id"
    ]
    row = next(r for r in wire.bootstrap()["records"] if r["id"] == cable)
    assert wire.wire_connect(
        cable,
        row["revision"],
        [{"device": switches[0], "port": "X3"}, {"device": switches[1], "port": "X3"}],
    )["ok"]
    cables.append(cable)
    return wire, rack, racks, switches, cables


def mutate(rack, operation, values):
    return rack.rack_organization(rack.bootstrap()["organizationRevision"], operation, values)


def test_cpd_shared_moves_delete_and_stale_rejection(workspace):
    wire, rack, racks, switches, cables = seed()
    before = {r["id"]: r for r in wire.bootstrap()["records"] if r["id"] in switches + cables}
    c1 = mutate(rack, "create", {"name": "Sala principal", "location": "Planta 1"})["id"]
    c2 = mutate(rack, "create", {"name": "Sala principal"})["id"]
    assert c1 != c2
    for r in racks:
        assert mutate(rack, "assign", {"id": c1, "rack": r})["ok"]
    snapshot = wire.bootstrap()
    assert len(snapshot["cpds"]) == 2
    assert all(r["data"]["location"]["cpd"] == c1 for r in snapshot["records"] if r["id"] in racks)
    stale = rack.bootstrap()["organizationRevision"]
    assert mutate(rack, "assign", {"id": c2, "rack": racks[0]})["ok"]
    assert not rack.rack_organization(stale, "edit", {"id": c1, "name": "Obsoleto"})["ok"]
    assert mutate(rack, "delete", {"id": c1, "target": c2})["ok"]
    assert all(r["location"]["cpd"] == c2 for r in rack.bootstrap()["records"])
    assert mutate(rack, "delete", {"id": c2})["ok"]
    assert not rack.bootstrap()["cpds"]
    assert all(not r["location"].get("cpd") for r in rack.bootstrap()["records"])
    after = {r["id"]: r for r in wire.bootstrap()["records"] if r["id"] in switches + cables}
    assert before == after
    assert not wire.rack_organization(
        wire.bootstrap()["organizationRevision"], "create", {"name": "No"}
    )["ok"]


def test_cpd_legacy_and_invalid_metadata_preserved(workspace):
    wire, rack, racks, _, _ = seed()
    path = Path(workspace["physicalDatabase"])
    document = json.loads(path.read_text())
    assert "cpdOrganization" not in document
    assert rack.bootstrap()["cpds"] == []
    assert not mutate(rack, "create", {"name": " "})["ok"]
    assert not mutate(rack, "assign", {"rack": racks[0], "id": "missing"})["ok"]
    assert json.loads(path.read_text()) == document
    document["cpdOrganization"] = {"schemaVersion": 99, "rooms": {}}
    path.write_text(json.dumps(document))
    before = path.read_bytes()
    assert not rack.bootstrap()["ok"]
    assert not wire.bootstrap()["ok"]
    assert path.read_bytes() == before


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_cpd_two_windows_topology_real_connections(workspace):
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    wire, rack, racks, switches, _cables = seed()
    room = mutate(rack, "create", {"name": "CPD Madrid", "description": "Sala A"})["id"]
    for r in racks:
        assert mutate(rack, "assign", {"id": room, "rack": r})["ok"]
    root = Path(__file__).resolve().parents[1]
    with playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 940})
        errors = []

        def open_page(service):
            page = context.new_page()
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.expose_function("rpc", lambda method, args: getattr(service, method)(*args))
            page.goto((root / "gui/launcher.html").as_uri())
            page.evaluate(
                "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
            )
            return page

        wp = open_page(wire)
        rp = open_page(rack)
        wp.locator("#wire-board").wait_for()
        rp.get_by_role("heading", name="CPD Madrid", exact=True).wait_for()
        assert rp.locator(".rack-cabinet").count() == 7
        assert wp.locator(".wire-node").count() == 7  # Los racks son contenedores.
        assert wp.locator(".physical-region").count() == 7
        assert wp.locator("#wire-lines path").count() == 8
        wp.locator('[data-nav="fit"]').click()
        # Un clic de puerto selecciona, sin sugerir conexiones.
        wp.locator(f'[data-node="{switches[0]}"] [data-port="X1"]').click(force=True)
        assert not wp.locator("#detail").is_visible()
        assert wp.locator(f'[data-node="{switches[0]}"] .wire-ports').evaluate(
            "e=>e.scrollHeight<=e.clientHeight"
        )
        # El extremo coincide con el centro real del puerto tras cambiar zoom.
        wp.locator('[data-nav="in"]').click()
        delta = wp.evaluate(
            """id=>{const e=wireGraph.edges.find(e=>e.a?.device===id),a=wireAnchor(e.a),port=document.querySelector('[data-node="'+id+'"] [data-port="'+e.a.port+'"]'),r=port.getBoundingClientRect(),w=document.querySelector('#wire-world').getBoundingClientRect();return Math.hypot(a.x-(r.x+r.width/2-w.x)/camera.z,a.y-(r.y+r.height/2-w.y)/camera.z)}""",
            switches[0],
        )
        assert delta < 0.01
        wp.locator('[data-level="outside"]').click()
        assert wp.locator(".wire-node").count() == 7
        assert wp.locator("#wire-lines path").count() == 7  # Dos enlaces A-B agrupados.
        assert "2 cables" in wp.locator("#wire-lines").text_content()
        wp.locator("#physical-bundles").uncheck()
        assert wp.locator("#wire-lines path").count() == 8
        wp.locator(f'[data-node="{racks[0]}"] strong').dblclick()
        assert wp.locator("#physical-rack").input_value() == racks[0]
        assert wp.locator(f'[data-node="{switches[0]}"]').count() == 1
        assert wp.locator("#wire-lines path").count() == 3
        # CPD creado desde LANRACK visible en LANWIRE al actualizar.
        rp.locator("#rack-new-room").click()
        rp.locator('[name="name"]').fill("CPD Barcelona")
        rp.locator("#submit").click()
        rp.wait_for_function("!document.querySelector('#detail').open")
        second = next(c for c in rack.bootstrap()["cpds"] if c["name"] == "CPD Barcelona")
        rp.locator(f'[data-rack-open="{racks[0]}"]').click()
        rp.locator("#rack-assign").click()
        rp.locator('[name="id"]').select_option(second["id"])
        rp.locator("#submit").click()
        rp.wait_for_function("!document.querySelector('#detail').open")
        wp.evaluate("refresh()")
        wp.locator('[data-level="outside"]').click()
        wp.locator("#physical-rack").select_option("")
        assert "CPD Barcelona" in wp.locator(".physical-region").all_text_contents()
        assert len(wire.bootstrap()["records"]) == 22
        wp.locator('[data-nav="fit"]').click()
        assert wp.evaluate(
            """()=>{const ns=[...document.querySelectorAll('[data-node]')].map(n=>n.getBoundingClientRect());return !ns.some((a,i)=>ns.some((b,j)=>j>i&&a.left<b.right&&a.right>b.left&&a.top<b.bottom&&a.bottom>b.top));}"""
        )
        assert wp.evaluate(
            """()=>wireGraph.nodes.every(n=>{const group=physicalRegions.find(r=>r.id===(n.data.location?.cpd||'')),p=wirePositions[n.id],s=physicalSize(n);return group&&p.x>=group.x&&p.y>=group.y&&p.x+s.w<=group.x+group.w&&p.y+s.h<=group.y+group.h})"""
        )
        wp.screenshot(path=str(root / "tmp/cpd-lanwire-general.png"))
        rp.screenshot(path=str(root / "tmp/cpd-lanrack.png"))
        for page in (wp, rp):
            page.set_viewport_size({"width": 960, "height": 650})
            assert page.locator("footer").bounding_box()["y"] < 650
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        assert not errors, errors
        browser.close()
