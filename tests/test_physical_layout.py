"""Pure graph layout regression, no browsers or user data."""

import subprocess
from pathlib import Path

import pytest
from test_launcher_gui import workspace as workspace


def test_layered_layout_invariants():
    playwright = pytest.importorskip("playwright")
    node = Path(playwright.__file__).parent / "driver/node"
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [str(node), str(root / "tests/physical_layout.cjs"), str(root / "gui/physical-gui.js")],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.skipif(
    __import__("os").environ.get("LANCTL_GUI_BROWSER_TESTS") != "1",
    reason="optional browser runtime",
)
def test_reorganize_real_wire_diagram(workspace):
    import os

    from test_launcher_gui import api
    from test_physical_placement_gui import open_page

    wire = api("lanwire")
    router = wire.wire_create({"kind": "router.gateway", "prefix": "RT", "name": "Router"})["id"]
    switch = wire.wire_create({"kind": "switch.24ports", "prefix": "SW", "name": "Switch"})["id"]
    pcs = [
        wire.wire_create({"kind": "pc.1port", "prefix": "PC", "name": f"PC {i + 1}"})["id"]
        for i in range(3)
    ]
    for index, device in enumerate([router, *pcs]):
        cable = wire.wire_create({"kind": "wire.copper", "prefix": "WL"})["id"]
        rows = {r["id"]: r for r in wire.bootstrap()["records"]}
        from lanctl.apps.wire.topology import compatible_connection

        end = next(
            port
            for port, data in rows[device]["data"]["ports"].items()
            if compatible_connection(rows[cable]["data"], data)[0]
        )
        result = wire.wire_connect(
            cable,
            rows[cable]["revision"],
            [
                {"device": switch, "port": list(rows[switch]["data"]["ports"])[index]},
                {"device": device, "port": end},
            ],
        )
        assert result["ok"], result
    before = wire._service.database.path.read_bytes()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, wire)
        page.wait_for_selector("#wire-board")
        page.evaluate("(id)=>{wirePositions[id]={x:123,y:456};render()}", switch)
        assert page.evaluate("(id)=>wirePositions[id]", switch) == {"x": 123, "y": 456}
        page.locator('[data-nav="layout"]').click()
        assert page.evaluate("(id)=>wirePositions[id]", switch) != {"x": 123, "y": 456}
        nodes = page.locator("[data-node]").evaluate_all(
            "(nodes)=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,h:r.height}})"
        )
        for i, a in enumerate(nodes):
            for b in nodes[i + 1 :]:
                assert (
                    a["x"] + a["w"] <= b["x"] + 1
                    or b["x"] + b["w"] <= a["x"] + 1
                    or a["y"] + a["h"] <= b["y"] + 1
                    or b["y"] + b["h"] <= a["y"] + 1
                )
        assert wire._service.database.path.read_bytes() == before
        output = os.environ.get("LANCTL_LAYOUT_REVIEW_DIR")
        if output:
            destination = Path(output)
            destination.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(destination / "diagram.png"))
        browser.close()
