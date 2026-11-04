"""Settings contracts remain usable with all interface imports prohibited."""

import ast
import os
import subprocess
import sys
from pathlib import Path

from lanctl.apps.ip.interfaces.tui import keyboard, layout
from lanctl.shared import tui_keyboard, tui_layout


def test_historical_imports_are_compatible_aliases():
    for name in (
        "DEFAULT_TUI_KEY_BINDINGS",
        "CONFIGURABLE_TUI_KEYS",
        "FOOTER_ACTIONS",
        "normalize_key_bindings",
        "validate_key_bindings",
        "normalize_footer_actions",
    ):
        assert getattr(keyboard, name) is getattr(tui_keyboard, name)
    for name in (
        "TuiLayout",
        "adaptive_layout",
        "normalize_cli_percent",
        "normalize_panel_layout",
        "normalize_column_spec",
        "allocate_column_widths",
        "DEFAULT_COLUMN_SPECS",
    ):
        assert getattr(layout, name) is getattr(tui_layout, name)


def test_core_and_shared_contracts_do_not_import_interface_modules():
    root = Path(__file__).resolve().parents[1] / "src/lanctl"
    files = [
        *root.joinpath("core").rglob("*.py"),
        root / "shared/tui_layout.py",
        root / "shared/tui_keyboard.py",
    ]
    violations = []
    for path in files:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = (
                [node.module or ""]
                if isinstance(node, ast.ImportFrom)
                else [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else []
            )
            if any(name.startswith("lanctl.apps.") and ".interfaces" in name for name in names):
                violations.append((str(path.relative_to(root)), node.lineno))
    assert not violations


def test_validation_works_in_cold_process_without_interfaces():
    source = Path(__file__).resolve().parents[1] / "src"
    script = """
import importlib.abc
import sys
class NoInterfaces(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.startswith('lanctl.apps.') and '.interfaces' in fullname:
            raise AssertionError('unexpected interface import: '+fullname)
sys.meta_path.insert(0, NoInterfaces())
from lanctl.core.config import DOCUMENT_DEFAULTS, config_from_document, canonical_config
from lanctl.core.settings_catalog import validate_value
from lanctl.core.settings_policy import SettingsContext, prepare_program_changes
config = config_from_document(DOCUMENT_DEFAULTS)
assert validate_value('tui.cliHeightPercent', 40, 35) == 40
assert validate_value('tui.panelLayout', 'top', 'cli.bottom') == 'cli.top'
changed = prepare_program_changes(config, {'tui.keyBindings.help':'F4'}, SettingsContext('tui', launcher='lanip'))
assert canonical_config(changed)['tui']['keyBindings']['help'] == 'F4'
try:
    prepare_program_changes(config, {'tui.keyBindings.help':'F2'}, SettingsContext('tui', launcher='lanip'))
except ValueError:
    pass
else:
    raise AssertionError('duplicate shortcut accepted')
"""
    environment = dict(os.environ, PYTHONPATH=str(source))
    completed = subprocess.run(
        [sys.executable, "-c", script], env=environment, capture_output=True, text=True, timeout=10
    )
    assert completed.returncode == 0, completed.stderr
