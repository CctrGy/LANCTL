from __future__ import annotations

import json
from pathlib import Path

from tools.generate_web_reference import generate, generate_data

ROOT = Path(__file__).resolve().parents[1]


def test_web_reference_catalog_covers_all_launchers_and_key_domains():
    data = generate_data()
    entries = data["entries"]
    launchers = {entry["name"] for entry in entries if entry["kind"] == "launcher"}
    categories = {entry["category"] for entry in entries}
    assert launchers == {"LANCTL", "LANIP", "LANWIRE", "LANRACK", "LANACCESS", "LANMON"}
    assert {"Proyectos", "Plugins y expansiones", "Archivos de documentación"} <= categories
    assert len({entry["id"] for entry in entries}) == len(entries)
    assert all(entry["compatibility"]["verified"] == data["meta"]["version"] for entry in entries)
    assert len(data["workflows"]) >= 8
    assert all(len(workflow["steps"]) >= 5 for workflow in data["workflows"])
    assert all(
        workflow["compatibility"]["verified"] == data["meta"]["version"]
        for workflow in data["workflows"]
    )
    assert {
        "workflow-project-create-save",
        "workflow-plugin-import",
        "workflow-ssh-credentials",
    } <= {workflow["id"] for workflow in data["workflows"]}
    entry_ids = {entry["id"] for entry in entries}
    for workflow in data["workflows"]:
        assert set(workflow["related"]) <= entry_ids
        assert all((ROOT / "docs" / name).is_file() for name in workflow["docs"])


def test_web_reference_artifact_is_current_and_self_contained():
    artifact = ROOT / "reference" / "catalog.js"
    assert artifact.read_text(encoding="utf-8") == generate()
    html = (ROOT / "reference" / "index.html").read_text(encoding="utf-8")
    assert "catalog.js" in html
    assert "Explorar por acciones" in html
    assert "compatibilityLabel" in (ROOT / "reference" / "assets" / "reference.js").read_text(
        encoding="utf-8"
    )
    assert 'id="catalog"' in html and "hidden" in html
    assert "https://cdn." not in html
    payload = artifact.read_text(encoding="utf-8").split(" = ", 1)[1].removesuffix(";\n")
    assert json.loads(payload)["meta"]["entryCount"] > 20
