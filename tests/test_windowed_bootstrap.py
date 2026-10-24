"""P73: GUI-only routing without changing console launcher behavior."""

import importlib
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from lanctl.apps.suite import processes
from lanctl.bootstrap import gui


@pytest.mark.parametrize(
    "launcher", ["lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"]
)
def test_windowed_host_routes_existing_bootstrap(monkeypatch, launcher):
    module = importlib.import_module(gui._APPLICATIONS[launcher])
    main = Mock(return_value=0)
    monkeypatch.setattr(module, "main", main)
    assert gui.main([launcher]) == 0
    main.assert_called_once_with(["--gui"])


def test_first_scan_only_for_lanip_and_errors_are_logged(monkeypatch):
    from lanctl.core.errors import errors

    module = importlib.import_module(gui._APPLICATIONS["lanip"])
    main = Mock(return_value=0)
    monkeypatch.setattr(module, "main", main)
    assert gui.main(["lanip", "--first-scan"]) == 0
    main.assert_called_once_with(["--gui", "--first-scan"])
    logged = Mock(return_value=SimpleNamespace(message="Invalid", error_id="test-id"))
    notify = Mock()
    monkeypatch.setattr(errors, "from_exception", logged)
    monkeypatch.setattr(gui, "_notify_failure", notify)
    for arguments in (["powershell"], ["lanwire", "--first-scan"], ["lanctl", "--cli"]):
        assert gui.main(arguments) == 2
    assert logged.call_count == notify.call_count == 3
    assert "test-id" in notify.call_args.args[0]


def test_start_failure_preserves_code_and_reports_without_console(monkeypatch):
    module = importlib.import_module(gui._APPLICATIONS["lanctl"])
    monkeypatch.setattr(module, "main", lambda _: 17)
    notify = Mock()
    monkeypatch.setattr(gui, "_notify_failure", notify)
    assert gui.main(["lanctl"]) == 17
    assert "17" in notify.call_args.args[0]


def test_frozen_gui_uses_host_but_cli_and_legacy_installation_keep_console(tmp_path, monkeypatch):
    monkeypatch.setattr(processes.sys, "frozen", True, raising=False)
    monkeypatch.setattr(processes.sys, "platform", "win32")
    monkeypatch.setattr(processes.sys, "executable", str(tmp_path / "LANCTL.exe"))
    assert processes.launcher_command("lanip", "--gui") == [str(tmp_path / "lanip.exe"), "--gui"]
    host = tmp_path / "lanctl-window.exe"
    host.touch()
    for launcher in gui._APPLICATIONS:
        assert processes.launcher_command(launcher, "--gui") == [str(host), launcher]
        for mode in ("--cli", "--tui", "--version"):
            assert processes.launcher_command(launcher, mode) == [
                str(tmp_path / (launcher + ".exe")),
                mode,
            ]
