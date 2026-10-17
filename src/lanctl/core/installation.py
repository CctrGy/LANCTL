"""Initial installation preferences applied once, without activating optional plugins."""

from lanctl.core import config
from lanctl.core.file_transaction import locked_file
from lanctl.core.gui_preferences import validate_preferences
from lanctl.core.paths import application_path
from lanctl.core.plugins.builtin import bootstrap_builtin_plugins
from lanctl.core.plugins.selection import OPTIONAL_PLUGINS, initialize_selection


def initialize_defaults(*, theme="graphite", plugins="all"):
    preferences = validate_preferences(
        {"theme": theme, "density": "comfortable", "fontScale": 1.0, "reducedMotion": False}
    )
    selected = (
        list(OPTIONAL_PLUGINS)
        if plugins == "all"
        else []
        if plugins == "none"
        else plugins.split(",")
    )
    if not all(item in OPTIONAL_PLUGINS for item in selected):
        raise ValueError("selección de plugins opcionales desconocida")
    with locked_file(config.CONFIG_PATH):
        existing = config.CONFIG_PATH.exists()
        settings = config.load_config()
        if not existing:
            settings["guiPreferences"] = {"schemaVersion": 1, **preferences}
            config.save_config(settings)
        root = application_path(settings["plugins"])
        actual = initialize_selection(root, selected)
    bootstrap_builtin_plugins(root)
    return {"preservedConfiguration": existing, "selected": sorted(actual), "activated": False}
