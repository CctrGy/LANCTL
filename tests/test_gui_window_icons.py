"""P43: desktop entry points must supply an icon accepted by their native backend."""

import importlib
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch

import pytest

from lanctl.core.resources import bundled_path

ENTRY_POINTS = (
    ("lanctl.apps.suite.gui", "SuiteApi", "lanctl"),
    ("lanctl.apps.ip.interfaces.gui.desktop", "DesktopApi", "lanip"),
)


def start_desktop(module_name, api_name, *arguments):
    """Run the real entry point without opening a window or reading user settings."""
    module = importlib.import_module(module_name)
    webview = SimpleNamespace(create_window=Mock(return_value=MagicMock()), start=Mock())
    with (
        patch.dict(sys.modules, {"webview": webview}),
        patch.object(module, api_name),
        patch("lanctl.apps.access.root_control.RootInterfaceAgent"),
        patch("lanctl.core.session.current_session", return_value=None),
    ):
        assert module.run_gui(*arguments) == 0
    webview.start.assert_called_once()
    return Path(webview.start.call_args.kwargs["icon"])


@pytest.fixture(params=(False, True), ids=("source", "pyinstaller"))
def resource_root(request, tmp_path, monkeypatch):
    source = bundled_path("assets/launcher-icons")
    if not request.param:
        monkeypatch.delattr(sys, "_MEIPASS", raising=False)
        return source
    # Exercise the same layout as the one-file distribution, including spaces in paths.
    extracted = tmp_path / "unpacked LANCTL"
    icons = extracted / "assets/launcher-icons"
    shutil.copytree(source, icons)
    monkeypatch.setattr(sys, "_MEIPASS", str(extracted), raising=False)
    return icons


@pytest.mark.parametrize("module_name,api_name,launcher", ENTRY_POINTS)
@pytest.mark.parametrize("platform", ("win32", "linux", "darwin"))
def test_gui_start_selects_backend_compatible_icon(
    module_name, api_name, launcher, platform, resource_root, monkeypatch
):
    # Import first: changing sys.platform should affect icon selection only.
    importlib.import_module(module_name)
    monkeypatch.setattr(sys, "platform", platform)
    path = start_desktop(module_name, api_name)
    suffix = "ico" if platform == "win32" else "png"
    assert path == resource_root / f"{launcher}.{suffix}"
    header = b"\x00\x00\x01\x00" if platform == "win32" else b"\x89PNG\r\n\x1a\n"
    assert path.read_bytes().startswith(header)


@pytest.mark.skipif(sys.platform != "win32", reason="System.Drawing is the Windows GUI backend")
@pytest.mark.parametrize("module_name,api_name,launcher", ENTRY_POINTS)
def test_windows_accepts_actual_gui_icon(module_name, api_name, launcher, resource_root):
    assert_windows_icon(start_desktop(module_name, api_name))


@pytest.mark.skipif(sys.platform != "win32", reason="System.Drawing is the Windows GUI backend")
@pytest.mark.parametrize("launcher", ("lanwire", "lanrack", "lanaccess", "lanmon"))
def test_specialized_launcher_supplies_native_icon(launcher, resource_root):
    path = start_desktop("lanctl.apps.suite.launcher_gui", "LauncherApi", launcher)
    assert_windows_icon(path)
    assert path == resource_root / f"{launcher}.ico"


def assert_windows_icon(path):
    clr = pytest.importorskip("clr", reason="Requires the Windows GUI optional dependencies")
    clr.AddReference("System.Drawing")
    drawing = importlib.import_module("System.Drawing")
    # This exact constructor raised the unhandled ArgumentException in P43.
    icon = drawing.Icon(str(path))
    try:
        assert icon.Width > 0 and icon.Height > 0
        assert icon.Handle.ToInt64() != 0
    finally:
        icon.Dispose()
