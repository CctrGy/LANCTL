"""Versioned project diagram JSON survives reload and VLF reopening."""

import json
import os
from copy import deepcopy

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_project_sync import projects

VIEW = json.dumps(["inside", "", ""], separators=(",", ":"))
LAYOUT = {
    "schemaVersion": 1,
    "positions": {"SW-00": {"x": 123, "y": 456}},
    "camera": {"x": 20, "y": 30, "z": 0.75},
}


def test_diagram_roundtrip_conflict_and_invalid_input(workspace, tmp_path):
    from lanctl.apps.wire.idf.database import IDFDatabaseManager
    from lanctl.core.projects.physical import workspace_path
    from lanctl.core.projects.save_policy import save_active_project
    from lanctl.core.projects.workspace import prepare_project_workspace

    project, _ = projects(workspace, tmp_path)
    wire = api("lanwire")
    original = wire.bootstrap()["diagramRevisions"]
    assert original == {}
    first = wire.wire_diagram(VIEW, None, LAYOUT)
    assert first["ok"], first
    before = wire._service.database.path.read_bytes()
    assert not wire.wire_diagram(VIEW, None, LAYOUT)["ok"]
    assert wire._service.database.path.read_bytes() == before
    bad = deepcopy(LAYOUT)
    bad["camera"]["z"] = float("nan")
    assert not wire.wire_diagram(VIEW, first["diagramRevisions"][VIEW], bad)["ok"]
    assert wire._service.database.path.read_bytes() == before
    other = json.dumps(["outside", "", ""])
    assert wire.wire_diagram(other, None, LAYOUT)["ok"]
    assert save_active_project(force=True).saved
    reopened = prepare_project_workspace(project, root=tmp_path / "reopened")
    from lanctl.apps.wire.xfile import read

    database = IDFDatabaseManager(workspace_path(reopened.database))
    data = read(database.path)
    assert data["diagramLayouts"]["views"][VIEW] == LAYOUT
    assert len(data["diagramLayouts"]["views"]) == 2


@pytest.mark.parametrize(
    "bounds",
    [
        {"x": 0, "y": 0, "w": -1, "h": 200},
        {"x": float("nan"), "y": 0, "w": 200, "h": 200},
        {"x": 0, "y": 0, "w": 200, "h": 10_000_001},
    ],
)
def test_invalid_region_preserves_project(workspace, tmp_path, bounds):
    projects(workspace, tmp_path)
    wire = api("lanwire")
    assert wire.wire_diagram(VIEW, None, LAYOUT)["ok"]
    before = wire._service.database.path.read_bytes()
    layout = deepcopy(LAYOUT)
    layout["regions"] = {"RK-00": bounds}
    revision = wire.bootstrap()["diagramRevisions"][VIEW]
    assert not wire.wire_diagram(VIEW, revision, layout)["ok"]
    assert wire._service.database.path.read_bytes() == before


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_frontend_layout_survives_empty_local_storage(workspace, tmp_path):
    from test_physical_placement_gui import open_page

    from lanctl.core.projects.save_policy import save_active_project

    projects(workspace, tmp_path)
    wire = api("lanwire")
    identifier = wire.wire_create({"kind": "switch.24ports", "prefix": "SW"})["id"]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, wire)
        page.wait_for_selector("#wire-board")
        result = page.evaluate(
            """async id=>{
          wirePositions[id]={x:321,y:654};camera={x:17,y:29,z:.75};
          wireSavePositions();await wireFlushDiagram();
          return {key:wireDiagramView(),value:state.diagramLayouts.views[wireDiagramView()]};
        }""",
            identifier,
        )
        assert result["value"]["positions"][identifier] == {"x": 321, "y": 654}
        assert save_active_project(force=True).saved
        saved = page.evaluate(
            """async id => {
          wirePositions[id]={x:777,y:654};wireSavePositions();
          return await call('save_project');
        }""",
            identifier,
        )
        assert saved["ok"], saved
        page.close()
        page = open_page(browser, api("lanwire"), init_script="localStorage.clear()")
        page.wait_for_selector("#wire-board")
        page.evaluate("()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))")
        assert page.evaluate("(id)=>wirePositions[id]", identifier) == {"x": 777, "y": 654}, (
            page.evaluate(
                "({layouts:state.diagramLayouts, project:state.project, scope:wireDiagramScope,key:wireDiagramView(),storage:state.storage})"
            )
        )
        assert page.evaluate("camera") == {"x": 17, "y": 29, "z": 0.75}
        assert page.evaluate("wireDiagramUnsaved.size") == 0
        browser.close()


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_resize_region_pushes_other_rack_and_reopens(workspace, tmp_path):
    from test_physical_placement_gui import open_page

    projects(workspace, tmp_path)
    wire = api("lanwire")
    racks = [
        wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"] for _ in range(2)
    ]
    nodes = [
        wire.wire_create({"kind": "switch.24ports", "prefix": "SW", "rack": rack, "unit": 1})["id"]
        for rack in racks
    ]
    before = wire._service.database.all()
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, wire)
        page.wait_for_selector("#wire-board")
        page.evaluate(
            """({racks,nodes})=>{
          wireRegionFrames={[racks[0]]:{x:0,y:0,w:650,h:400},[racks[1]]:{x:800,y:0,w:650,h:400}};
          wirePositions={[nodes[0]]:{x:60,y:80},[nodes[1]]:{x:860,y:80}};
          camera={x:0,y:0,z:1};render();wirePaint();
        }""",
            {"racks": racks, "nodes": nodes},
        )
        handle = page.locator(f'[data-region-id="{racks[0]}"][data-resize-side="e"]')
        bounds = handle.bounding_box()
        page.mouse.move(bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2)
        page.mouse.down()
        page.mouse.move(
            bounds["x"] + bounds["width"] / 2 + 300, bounds["y"] + bounds["height"] / 2, steps=8
        )
        page.mouse.up()
        page.evaluate("()=>wireFlushDiagram()")
        actual = page.evaluate("({positions:wirePositions,regions:wireRegionFrames})")
        assert actual["regions"][racks[0]]["w"] == 950
        assert actual["regions"][racks[1]]["x"] >= 990
        assert actual["positions"][nodes[0]] == {"x": 60, "y": 80}
        assert actual["positions"][nodes[1]]["x"] >= 1050
        assert wire._service.database.all() == before
        # Cancelling a second drag restores both the resized region and pushed blocks.
        handle = page.locator(f'[data-region-id="{racks[0]}"][data-resize-side="e"]')
        bounds = handle.bounding_box()
        page.mouse.move(bounds["x"] + bounds["width"] / 2, bounds["y"] + bounds["height"] / 2)
        page.mouse.down()
        page.mouse.move(bounds["x"] + 130, bounds["y"], steps=4)
        page.keyboard.press("Escape")
        page.mouse.up()
        assert page.evaluate("wireRegionFrames") == actual["regions"]
        assert page.evaluate("wirePositions") == actual["positions"]
        top = page.locator(f'[data-region-id="{racks[0]}"][data-resize-side="n"]')
        top.focus()
        page.keyboard.press("ArrowUp")
        assert page.evaluate("wireRegionFrames")[racks[0]]["y"] == -20
        actual = page.evaluate("({positions:wirePositions,regions:wireRegionFrames})")
        output = os.environ.get("LANCTL_LAYOUT_REVIEW_DIR")
        if output:
            from pathlib import Path

            destination = Path(output)
            destination.mkdir(parents=True, exist_ok=True)
            page.evaluate("wireFit()")
            page.screenshot(path=str(destination / "resize-regions.png"))
        saved = page.evaluate("()=>call('save_project')")
        assert saved["ok"], saved
        page.close()
        page = open_page(browser, api("lanwire"), init_script="localStorage.clear()")
        page.wait_for_selector("#wire-board")
        assert page.evaluate("wireRegionFrames") == actual["regions"]
        assert page.evaluate("wirePositions") == actual["positions"]
        browser.close()
