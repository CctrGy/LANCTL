"""P118 local GUI RPCs, isolated from windows, projects and real preferences."""

import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from lanctl.apps.suite.shortcuts_gui import ShortcutGuiMixin

pytestmark = pytest.mark.skipif(
    not sys.platform.startswith("linux"), reason="Linux desktop shortcut fixtures"
)


class Adapter(ShortcutGuiMixin):
    def __init__(self):
        self._lock = threading.RLock()
        self._desktop = SimpleNamespace(_window=None)
        self.failures = []

    def _respond(self, action, operation):
        with self._lock:
            try:
                return {"ok": True, **operation()}
            except (ValueError, OSError, RuntimeError) as exc:
                self.failures.append((action, exc))
                return {"ok": False, "error": str(exc)}


@pytest.fixture
def form(tmp_path):
    executable = tmp_path / "lanctl"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o755)
    return {"distribution": str(tmp_path), "launcher": "lanctl", "mode": "tui", "name": "Acceso"}


def test_preview_then_create_once(form, tmp_path):
    api = Adapter()
    preview = api.preview_shortcut(form)
    assert preview["ok"]
    assert preview["arguments"] == ["--tui"]
    assert not (tmp_path / "Acceso.desktop").exists()
    assert api.create_shortcut(preview["token"])["ok"]
    original = (tmp_path / "Acceso.desktop").read_bytes()
    assert not api.create_shortcut(preview["token"])["ok"]
    assert (tmp_path / "Acceso.desktop").read_bytes() == original


def test_invalid_preview_invalidates_previous(form):
    api = Adapter()
    preview = api.preview_shortcut(form)
    assert not api.preview_shortcut({**form, "name": "../bad"})["ok"]
    assert not api.create_shortcut(preview["token"])["ok"]


def test_new_preview_invalidates_previous(form):
    api = Adapter()
    first = api.preview_shortcut(form)
    second = api.preview_shortcut({**form, "name": "Otro"})
    assert not api.create_shortcut(first["token"])["ok"]
    assert api.create_shortcut(second["token"])["ok"]


@pytest.mark.parametrize("token", [None, {}, "wrong"])
def test_no_preview_no_creation(token):
    assert not Adapter().create_shortcut(token)["ok"]


def test_collision_retains_original_and_requires_new_preview(form, tmp_path):
    api = Adapter()
    preview = api.preview_shortcut(form)
    target = tmp_path / "Acceso.desktop"
    target.write_text("original")
    assert not api.create_shortcut(preview["token"])["ok"]
    assert isinstance(api.failures[-1][1], FileExistsError)
    assert target.read_text() == "original"
    assert not api.create_shortcut(preview["token"])["ok"]


@pytest.mark.parametrize("values", [None, [], {"name": []}])
def test_malformed_form(values):
    api = Adapter()
    assert not api.preview_shortcut(values)["ok"]
    assert str(api.failures[-1][1]) == "SHORTCUT.INVALID_FORM"


def test_gui_not_installed(form):
    api = Adapter()
    with patch("lanctl.apps.suite.shortcuts_gui.importlib.util.find_spec", return_value=None):
        assert not api.preview_shortcut({**form, "mode": "gui"})["ok"]
        assert "gui" in api.shortcut_options()["modes"]
        assert not api.shortcut_options()["guiAvailable"]


def test_picker_cancellation_preserves_form():
    api = Adapter()
    api._desktop._window = SimpleNamespace(create_file_dialog=lambda *args, **kwargs: None)
    with patch.dict("sys.modules", webview=SimpleNamespace(OPEN_DIALOG=1, FOLDER_DIALOG=2)):
        result = api.select_shortcut_path("destination")
    assert result == {"ok": True, "path": "", "cancelled": True}


def test_picker_kind_restricted():
    api = Adapter()
    assert not api.select_shortcut_path("project")["ok"]


def test_unsupported_platform_cannot_preview(form):
    api = Adapter()
    with patch("lanctl.apps.suite.shortcuts_gui.sys.platform", "darwin"):
        assert not api.shortcut_options()["supported"]
        assert not api.preview_shortcut(form)["ok"]


def test_form_preview_confirmation_and_cancel_without_browser():
    import subprocess
    from pathlib import Path

    playwright = pytest.importorskip("playwright")
    node = Path(playwright.__file__).parent / "driver/node"
    if not node.is_file():
        pytest.skip("Bundled Node runtime unavailable")
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [str(node), str(root / "tests/shortcut_form.cjs"), str(root / "gui/suite-shortcuts.js")],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_real_suite_rpc_works_without_project(form):
    from lanctl.apps.suite.gui import SuiteApi

    api = SuiteApi.__new__(SuiteApi)
    api._lock = threading.RLock()
    with patch("lanctl.core.config.load_config", return_value={}):
        preview = api.preview_shortcut(form)
        assert preview["ok"]
        assert api.create_shortcut(preview["token"])["ok"]


def test_real_suite_failure_keeps_diagnostic():
    from lanctl.apps.suite.gui import SuiteApi

    api = SuiteApi.__new__(SuiteApi)
    api._lock = threading.RLock()
    event = SimpleNamespace(
        message="original", error_id="event-id", to_dict=lambda: {"origin": "original"}
    )
    with (
        patch("lanctl.core.config.load_config", return_value={}),
        patch("lanctl.core.errors.errors.from_exception", return_value=event) as report,
    ):
        result = api.create_shortcut("not-previewed")
    assert not result["ok"]
    assert result["errorId"] == "event-id"
    assert result["errorDetails"] == {"origin": "original"}
    assert report.call_args.kwargs["origin"] == "LANCTL.Suite.GUI.ShortcutCreate"
    assert str(report.call_args.args[0]) == "SHORTCUT.PREVIEW_REQUIRED"
