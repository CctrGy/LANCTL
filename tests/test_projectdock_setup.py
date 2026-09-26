import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "setup_projectdock", ROOT / "tools/setup_projectdock.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_preview_is_read_only(tmp_path):
    before = list(tmp_path.iterdir())
    result = MODULE.prepare(tmp_path, sys.executable)
    assert result["apply"] is False
    assert result["trusted"] is False
    assert result["launcher_created"] is False
    assert list(tmp_path.iterdir()) == before


def test_apply_is_local_and_preserves_existing_configuration(tmp_path):
    MODULE.prepare(tmp_path, sys.executable, True)
    config = json.loads((tmp_path / ".project/project.json").read_text())
    assert config["python"] == sys.executable
    assert config["environment"]["LANCTL_DATA_DIR"] == "{root}/.project/lanctl-data"
    assert not (tmp_path / "run.exe").exists()
    sentinel = tmp_path / ".project/recipes/start.json"
    sentinel.write_text('{"custom": true}')
    with pytest.raises(FileExistsError):
        MODULE.prepare(tmp_path, sys.executable, True)
    assert sentinel.read_text() == '{"custom": true}'
    assert not list(tmp_path.glob(".project-setup-*"))


def test_recipe_mapping_preserves_specialized_implementations():
    recipes = json.loads(
        (ROOT / "repositoryTerminal/projectdock/recipes.json").read_text(encoding="utf-8")
    )
    names = [item["name"] for item in recipes]
    assert len(names) == len(set(names))
    items = {item["name"]: item for item in recipes}
    assert items["start"]["io"] == "inherit"
    assert items["start"]["command"] == ["{python}", "{root}/lanctl.py"]
    assert items["build-legacy"]["command"][-1] == "LANCTL.spec"
    assert items["repository-build"]["command"][-2:] == [
        "{root}/repositoryTerminal/repository.ps1",
        "build",
    ]
    for name in ["repository-build", "repository-install", "repository-remote"]:
        assert items[name + "-plan"]["command"] == [*items[name]["command"], "-DryRun"]
    assert "terminal-sign" in items
    assert all(isinstance(arg, str) for item in recipes for arg in item.get("command", []))
    assert items["test"]["steps"] == ["test-isolated", "test-paths"]
    assert items["test-paths"]["environment"]["LANCTL_DATA_DIR"] == ""
