"""P132 outlet metadata, validation and real frontend rendering."""

import os
from copy import deepcopy

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace


def test_outlet_metadata_validation_and_legacy(workspace):
    wire = api("lanwire")
    for kind in ("schuko", "iec-c13"):
        result = wire.wire_create(
            {
                "kind": "pdu",
                "prefix": "PD",
                "powerOutlets": {"schemaVersion": 1, "type": kind, "count": 8},
            }
        )
        assert result["ok"], result
        record = next(r for r in wire._service.snapshot()["records"] if r["id"] == result["id"])
        assert record["data"]["powerOutlets"]["type"] == kind
        assert record["data"]["ports"] == {}
        before = deepcopy(record)
        assert not wire.wire_update(
            record["id"],
            record["revision"],
            {"powerOutlets": {"schemaVersion": True, "type": kind, "count": 8}},
        )["ok"]
        assert (
            next(r for r in wire._service.snapshot()["records"] if r["id"] == record["id"])
            == before
        )
    for count in (0, 25, True, 1.5):
        assert not wire.wire_create(
            {
                "kind": "pdu",
                "prefix": "PD",
                "powerOutlets": {"schemaVersion": 1, "type": "schuko", "count": count},
            }
        )["ok"]
    legacy = wire.wire_create({"kind": "pdu", "prefix": "PD"})["id"]
    record = next(r for r in wire._service.snapshot()["records"] if r["id"] == legacy)
    assert "powerOutlets" not in record["data"]
    assert wire.wire_update(legacy, record["revision"], {"name": "Preserved"})["ok"]
    assert (
        "powerOutlets"
        not in next(r for r in wire._service.snapshot()["records"] if r["id"] == legacy)["data"]
    )


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_pdu_create_edit_and_render(workspace, tmp_path):
    from test_physical_placement_gui import open_page, save_form
    from test_project_sync import projects

    project, _ = projects(workspace, tmp_path)
    wire = api("lanwire")
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ["LANCTL_CHROMIUM_EXECUTABLE"], headless=True
        )
        page = open_page(browser, api("lanrack"))
        page.wait_for_function("state.records !== undefined")
        page.evaluate("wireNew('pdu')")
        page.locator("[name=outletType]").select_option("schuko")
        page.locator("[name=outletCount]").fill("6")
        save_form(page)
        record = next(
            r for r in wire._service.snapshot()["records"] if r["data"]["type"] == "rack.pdu"
        )
        assert record["data"]["powerOutlets"]["count"] == 6
        svg = page.evaluate("(r)=>rackFace(r)", record)
        assert svg.count('data-outlet="schuko"') == 6
        page.evaluate("(r)=>fullDetails(r)", record)
        page.locator("[name=outletType]").select_option("iec-c13")
        page.locator("[name=outletCount]").fill("12")
        save_form(page)
        record = next(r for r in wire._service.snapshot()["records"] if r["id"] == record["id"])
        svg = page.evaluate("(r)=>rackFace(r)", record)
        assert svg.count('data-outlet="iec-c13"') == 12
        from lanctl.apps.wire.idf.database import IDFDatabaseManager
        from lanctl.core.projects.physical import workspace_path
        from lanctl.core.projects.save_policy import save_active_project
        from lanctl.core.projects.workspace import prepare_project_workspace

        assert save_active_project(force=True).saved
        reopened = prepare_project_workspace(project, root=tmp_path / "reopened")
        stored = IDFDatabaseManager(workspace_path(reopened.database)).get(record["id"])
        assert stored["data"]["powerOutlets"] == record["data"]["powerOutlets"]
        output = os.environ.get("LANCTL_PDU_REVIEW_DIR")
        if output:
            from pathlib import Path

            root = Path(output)
            root.mkdir(parents=True, exist_ok=True)
            css = (Path(__file__).resolve().parents[1] / "gui/launcher.css").read_text()
            svgs = []
            for kind in ("schuko", "iec-c13"):
                example = deepcopy(record)
                example["data"]["powerOutlets"] = {"schemaVersion": 1, "type": kind, "count": 8}
                svgs.append("<h2>" + kind + "</h2>" + page.evaluate("(r)=>rackFace(r)", example))
            page.set_content(
                "<style>"
                + css
                + "body{background:#12191d;color:#e0e8e4;padding:30px;font:16px sans-serif}.rack-face{height:auto;width:100%;margin-bottom:30px}</style>"
                + "".join(svgs)
            )
            page.screenshot(path=str(root / "pdu-outlets.png"), full_page=True)
        browser.close()
