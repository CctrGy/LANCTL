import multiprocessing
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from lanctl.core.coordination import Coordinator
from lanctl.core.gui_instance import GuiInstance
from lanctl.core.session import Session


@pytest.mark.parametrize("error", [ValueError("invalid config"), PermissionError("config denied")])
def test_startup_configuration_failure_keeps_existing_error_boundary(error):
    from lanctl.core.session import coordinated_launcher

    target = Mock()
    entry = coordinated_launcher("lanctl")(target)
    with (
        patch("lanctl.core.config.load_config", side_effect=error),
        patch("lanctl.core.errors.errors.from_exception") as report,
    ):
        assert entry([]) == 2
    target.assert_not_called()
    assert report.call_args.kwargs["origin"] == "LANCTL.Core.Coordination.Startup"


@pytest.mark.parametrize("preferred", ["cli", "tui", "gui"])
@pytest.mark.parametrize("explicit", [False, True])
def test_startup_preference_and_explicit_override(preferred, explicit):
    from lanctl.bootstrap.lanctl import main

    with (
        patch("lanctl.core.config.load_config", return_value={"startupInterface": preferred}),
        patch("lanctl.apps.suite.gui.run_gui", return_value=0) as gui,
        patch("lanctl.apps.suite.interfaces.run_console", return_value=0) as console,
    ):
        assert main(["--cli"] if explicit else []) == 0
    if preferred == "gui" and not explicit:
        gui.assert_called_once()
        console.assert_not_called()
    else:
        console.assert_called_once_with(tui=preferred == "tui" and not explicit)
        gui.assert_not_called()


def test_startup_preferences_persist_and_reject_invalid_values(tmp_path, monkeypatch):
    from lanctl.core import config
    from lanctl.core.settings_catalog import set_program_value

    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    set_program_value("startup.interface", "gui")
    set_program_value("startup.closeGuiOnLaunch", True)
    assert config.load_config()["startupInterface"] == "gui"
    assert config.load_config()["closeGuiOnLaunch"] is True
    before = config.CONFIG_PATH.read_bytes()
    with pytest.raises(ValueError):
        set_program_value("startup.interface", "unknown")
    assert config.CONFIG_PATH.read_bytes() == before


def _gui_worker(path, started, closed, focus):
    coordinator = Coordinator(path)
    with GuiInstance("lanip", coordinator=coordinator) as primary:
        assert primary
        session = Session("lanip", "gui", {}, coordinator=coordinator)
        session.handler = lambda _: focus.set()
        coordinator.heartbeat(session.id, controls=True)
        started.set()
        try:
            closed.wait(15)
        finally:
            session.close()


def test_single_gui_across_processes_other_launchers_and_crash_recovery(tmp_path):
    context = multiprocessing.get_context("spawn")
    started, closed, focused = (context.Event() for _ in range(3))
    coordinator = Coordinator(tmp_path / "runtime.db")
    process = context.Process(target=_gui_worker, args=(coordinator.path, started, closed, focused))
    process.start()
    try:
        assert started.wait(10)
        with GuiInstance("lanip", coordinator=coordinator) as primary:
            assert not primary
        assert focused.wait(2)
        with GuiInstance("lanctl", coordinator=coordinator) as primary:
            assert primary
        process.terminate()
        process.join(5)
        with GuiInstance("lanip", coordinator=coordinator) as primary:
            assert primary
    finally:
        if process.is_alive():
            closed.set()
            process.join(3)
        if process.is_alive():
            process.terminate()
        process.join(5)


@pytest.mark.parametrize("close", [True, False])
@pytest.mark.parametrize("failure", [False, True])
def test_gui_launch_closes_only_after_ready_when_enabled(close, failure):
    from lanctl.apps.suite.gui import SuiteApi

    api = SuiteApi.__new__(SuiteApi)
    from threading import RLock

    api._lock = RLock()
    api._desktop = SimpleNamespace(_window=Mock())
    with (
        patch("lanctl.apps.suite.gui.load_config", return_value={"closeGuiOnLaunch": close}),
        patch("lanctl.apps.suite.gui.subprocess.Popen"),
        patch(
            "lanctl.core.gui_instance.focus_gui",
            side_effect=TimeoutError("not ready") if failure else None,
        ),
    ):
        result = api.launch_gui("lanip")
    assert result["ok"] is not failure
    assert api._desktop._window.destroy.called is (close and not failure)
