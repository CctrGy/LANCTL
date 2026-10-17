import json
from unittest.mock import Mock

import pytest

from lanctl.core import config
from lanctl.core.installation import initialize_defaults
from lanctl.core.plugins.builtin import EXAMPLE_PLUGIN_ID, bootstrap_builtin_plugins
from lanctl.core.plugins.selection import OPTIONAL_PLUGINS, initialize_selection, selected_plugins


@pytest.fixture
def data(tmp_path, monkeypatch):
    monkeypatch.setenv("LANCTL_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("LANCTL_SECRET_DIR", str(tmp_path / "secrets"))
    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr("lanctl.core.errors.errors.from_exception", Mock())
    return tmp_path


def test_none_excludes_optional_bootstrap_but_preserves_base_theme(data):
    result = initialize_defaults(theme="forest", plugins="none")
    root = data / "plugins"
    assert result["selected"] == [] and result["activated"] is False
    assert (root / "lanctl.theme.default" / "plugin.info").exists()
    assert all(not (root / p).exists() for p in OPTIONAL_PLUGINS)
    bootstrap_builtin_plugins(root)
    assert all(not (root / p).exists() for p in OPTIONAL_PLUGINS)
    assert config.load_config()["guiPreferences"]["theme"] == "forest"


def test_update_preserves_initial_selection_preferences_and_permission_registry(data):
    initialize_defaults(theme="light", plugins=EXAMPLE_PLUGIN_ID)
    registry = data / "plugins" / "registry.json"
    registry.write_text('{"schemaVersion":1,"plugins":{}}')
    previous = registry.read_bytes()
    result = initialize_defaults(theme="midnight", plugins="all")
    assert result["preservedConfiguration"]
    assert selected_plugins(data / "plugins") == {EXAMPLE_PLUGIN_ID}
    assert config.load_config()["guiPreferences"]["theme"] == "light"
    assert registry.read_bytes() == previous


def test_read_only_repeated_example_bootstrap_does_not_rewrite(data, monkeypatch):
    root = data / "plugins"
    initialize_selection(root, [EXAMPLE_PLUGIN_ID])
    bootstrap_builtin_plugins(root)
    monkeypatch.setattr(
        "lanctl.core.plugins.builtin.atomic_write_json", Mock(side_effect=AssertionError("rewrite"))
    )
    bootstrap_builtin_plugins(root)


def test_corrupt_selection_fails_closed_and_unknown_ids_do_not_persist(data):
    root = data / "plugins"
    with pytest.raises(ValueError):
        initialize_selection(root, ["unknown.plugin"])
    assert not root.exists()
    root.mkdir()
    path = root / "bundled-selection.json"
    path.write_text(json.dumps({"schemaVersion": 1, "selected": ["unknown.plugin"]}))
    with pytest.raises(ValueError):
        bootstrap_builtin_plugins(root)
    assert len(list(root.iterdir())) == 1
