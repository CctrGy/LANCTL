import json

import pytest

from lanctl.core.config import load_config, update_config
from lanctl.core.gui_preferences import preferences_payload, save_preferences


@pytest.fixture
def config_path(tmp_path, monkeypatch):
    path = tmp_path / "config.json"
    monkeypatch.setattr("lanctl.core.config.CONFIG_PATH", path)
    monkeypatch.setattr("lanctl.core.gui_preferences.active_theme_extensions", list)
    return path


def test_defaults_are_read_only_and_five_complete_themes(config_path):
    result = preferences_payload()
    assert result["preferences"]["theme"] == "graphite"
    assert len(result["themes"]) == 5
    assert len({t["id"] for t in result["themes"]}) == 5
    assert not config_path.exists()
    assert result["theme"]["tokens"]["--color-accent"] == "#b2ef26"


def test_persistence_and_unrelated_config_preserved(config_path):
    update_config(lambda c: c.update({"workers": 13, "startupInterface": "tui"}))
    values = {"theme": "light", "density": "compact", "fontScale": 1.3, "reducedMotion": True}
    saved = save_preferences(values)
    assert preferences_payload() == saved
    assert load_config()["workers"] == 13
    assert load_config()["startupInterface"] == "tui"
    assert json.loads(config_path.read_text())["gui"] == {"schemaVersion": 1, **values}
    update_config(lambda c: c.update({"workers": 14}))
    assert preferences_payload() == saved


@pytest.mark.parametrize(
    "key,value",
    [
        ("theme", "evil"),
        ("density", []),
        ("fontScale", True),
        ("fontScale", 0.89),
        ("fontScale", 1.31),
        ("fontScale", float("nan")),
        ("fontScale", float("inf")),
        ("reducedMotion", "false"),
    ],
)
def test_invalid_values_do_not_write(config_path, key, value):
    values = preferences_payload()["preferences"]
    values[key] = value
    with pytest.raises(ValueError):
        save_preferences(values)
    assert not config_path.exists()


def test_unknown_schema_not_silently_overwritten(config_path):
    config_path.write_text(json.dumps({"schemaVersion": 2, "gui": {"schemaVersion": 99}}))
    with pytest.raises(ValueError, match="versión"):
        preferences_payload()
    assert json.loads(config_path.read_text())["gui"]["schemaVersion"] == 99


def test_only_explicit_plugin_overrides_and_preferences_unchanged(config_path, monkeypatch):
    from lanctl.core.plugins.extensions import Extension

    extension = Extension(
        "example.theme.custom",
        "theme",
        "example.theme",
        {
            "tokens": {"color.accent": "#112233"},
            "components": {"lanctl.primary-action": {"color.text": "#abcdef"}},
        },
    )
    monkeypatch.setattr("lanctl.core.gui_preferences.active_theme_extensions", lambda: [extension])
    result = preferences_payload()
    assert result["theme"]["tokens"]["--color-accent"] == "#112233"
    assert result["theme"]["tokens"]["--color-background"] == "#15181c"
    assert result["theme"]["components"]["lanctl.primary-action"]["--color-text"] == "#abcdef"
    assert result["effectivePlugin"] == extension.extension_id
    assert result["theme"]["pluginTokens"] == {"--color-accent": "#112233"}
    assert result["preferences"]["theme"] == "graphite"
    assert not config_path.exists()


def test_settings_catalog_categories_and_same_validation(config_path):
    from lanctl.core.settings_catalog import CATEGORIES, catalog, set_program_value

    entries = catalog(load_config())
    assert all(entry["category"] in CATEGORIES for entry in entries)
    assert CATEGORIES["gui"] == "Apariencia y GUI"
    with pytest.raises(ValueError):
        set_program_value("gui.fontScale", 20)
    set_program_value("gui.theme", "forest")
    assert preferences_payload()["preferences"]["theme"] == "forest"


def test_bundled_fallback_does_not_override_explicit_preset(config_path, monkeypatch):
    from lanctl.core.plugins.extensions import Extension

    fallback = Extension(
        "lanctl.theme.default.palette",
        "theme",
        "lanctl.theme.default",
        {"tokens": {"color.accent": "#25a9e8"}},
    )
    monkeypatch.setattr("lanctl.core.gui_preferences.active_theme_extensions", lambda: [fallback])
    payload = preferences_payload()
    assert payload["theme"]["tokens"]["--color-accent"] == "#b2ef26"
    assert payload["theme"]["pluginTokens"] == {}
    assert payload["effectivePlugin"] is None
