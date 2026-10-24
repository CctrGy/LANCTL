"""Physical console lifecycle must retain the project that owns each operation."""

from importlib import import_module
from io import StringIO
from pathlib import Path
from threading import Event, Thread
from unittest.mock import patch

import pytest
from test_launcher_gui import workspace as workspace
from test_physical_save_modes import saved_inventory, set_mode
from test_project_sync import projects

from lanctl.core.config import load_config
from lanctl.core.projects.console_session import PhysicalConsoleSession, physical_console_session
from lanctl.core.projects.save_policy import save_active_project, workspace_is_dirty
from lanctl.core.projects.workspace import activate_project_workspace

wire = import_module("lanctl.apps.wire.cli.main")
rack = import_module("lanctl.apps.rack.cli")


def test_wire_console_saves_on_close(workspace, tmp_path, monkeypatch):
    first, _ = projects(workspace, tmp_path)
    set_mode("automatic.toClose")
    commands = iter(["reserve PC-01 name=Console", "exit"])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))
    assert wire.main.__wrapped__(["--cli"]) == 0
    assert "PC-01" in saved_inventory(first)["records"]


@pytest.mark.parametrize("launcher", [wire, rack])
def test_console_follows_shared_project(workspace, tmp_path, monkeypatch, launcher):
    first, second = projects(workspace, tmp_path)
    set_mode()
    commands = iter(
        ["reserve PC-01 name=First", "reserve PC-02 name=Second", "exit"]
        if launcher is wire
        else ["add-element --kind tray --prefix TR", "add-element --kind tray --prefix PC", "exit"]
    )
    calls = 0

    def read(_):
        nonlocal calls
        calls += 1
        if calls == 2:
            activate_project_workspace(second)
            set_mode()
        return next(commands)

    monkeypatch.setattr("builtins.input", read)
    assert launcher.main.__wrapped__(["--cli"]) == 0
    assert load_config()["activeProject"] == second
    assert len(saved_inventory(first)["records"]) == 1
    assert len(saved_inventory(second)["records"]) == 1


@pytest.mark.parametrize("launcher", [wire, rack])
@pytest.mark.parametrize(
    ("mode", "saved"),
    [
        ("manual", False),
        ("manual.inCloseConsult", False),
        ("automatic.toClose", True),
        ("automatic.toScan", False),
        ("automatic.timeToSave", False),
        ("automatic.allChanges", True),
    ],
)
def test_one_shot_modes_never_prompt_or_start_timer(
    workspace, tmp_path, monkeypatch, launcher, mode, saved
):
    first, _ = projects(workspace, tmp_path)
    set_mode(mode)
    monkeypatch.setattr("builtins.input", lambda _: pytest.fail("noninteractive prompt"))
    monkeypatch.setattr(PhysicalConsoleSession, "start", lambda _: pytest.fail("one-shot timer"))
    args = (
        ["add", "PC"] if launcher is wire else ["add-element", "--kind", "tray", "--prefix", "TR"]
    )
    assert launcher.main.__wrapped__(args) == 0
    assert bool(saved_inventory(first)["records"]) == saved
    assert workspace_is_dirty(load_config()) != saved


@pytest.mark.parametrize("launcher", [wire, rack])
@pytest.mark.parametrize("answer", ["s", "n"])
def test_cancel_close_keeps_console_usable(workspace, tmp_path, monkeypatch, launcher, answer):
    first, _ = projects(workspace, tmp_path)
    set_mode("manual.inCloseConsult")
    create = "add PC" if launcher is wire else "add-element --kind tray --prefix TR"
    commands = iter([create, "exit", "c", create, "exit", "invalid", answer])
    monkeypatch.setattr("builtins.input", lambda _: next(commands))
    assert launcher.main.__wrapped__(["--cli"]) == 0
    assert len(saved_inventory(first)["records"]) == (2 if answer == "s" else 0)
    assert workspace_is_dirty(load_config()) == (answer == "n")


@pytest.mark.parametrize("launcher", [wire, rack])
def test_close_failure_can_retry_without_repeating_edit(workspace, tmp_path, monkeypatch, launcher):
    first, _ = projects(workspace, tmp_path)
    set_mode("automatic.toClose")
    commands = iter(
        ["add PC" if launcher is wire else "add-element --kind tray --prefix TR", "exit", "exit"]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(commands))
    calls = 0

    def save(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("disk full")
        return save_active_project(*args, **kwargs)

    with patch("lanctl.core.projects.console_session.save_active_project", side_effect=save):
        assert launcher.main.__wrapped__(["--cli"]) == 0
    assert calls == 2
    assert len(saved_inventory(first)["records"]) == 1


@pytest.mark.parametrize("launcher", [wire, rack])
@pytest.mark.parametrize("mode", ["manual.inCloseConsult", "automatic.toClose"])
def test_eof_does_not_spin_or_prompt(workspace, tmp_path, monkeypatch, launcher, mode):
    first, _ = projects(workspace, tmp_path)
    set_mode(mode)
    calls = 0

    def read(_):
        nonlocal calls
        calls += 1
        if calls == 1:
            return "add PC" if launcher is wire else "add-element --kind tray --prefix TR"
        assert calls == 2
        raise EOFError

    monkeypatch.setattr("builtins.input", read)
    assert launcher.main.__wrapped__(["--cli"]) == 0
    assert bool(saved_inventory(first)["records"]) == (mode == "automatic.toClose")


@pytest.mark.parametrize("launcher", [wire, rack])
def test_explicit_initial_project_database_stays_fixed(workspace, tmp_path, monkeypatch, launcher):
    first, second = projects(workspace, tmp_path)
    path = set_mode()["physicalDatabase"]
    calls = 0

    def read(_):
        nonlocal calls
        calls += 1
        if calls == 1:
            activate_project_workspace(second)
            set_mode()
            return "add PC" if launcher is wire else "add-element --kind tray --prefix TR"
        return "exit"

    monkeypatch.setattr("builtins.input", read)
    assert launcher.main.__wrapped__(["--database", path, "--cli"]) == 0
    assert len(saved_inventory(first)["records"]) == 1
    assert not saved_inventory(second)["records"]
    assert load_config()["activeProject"] == second


@pytest.mark.parametrize("launcher", [wire, rack])
def test_external_database_never_saves_active_vlf(workspace, tmp_path, monkeypatch, launcher):
    first, _ = projects(workspace, tmp_path)
    settings = set_mode("automatic.toClose")
    wire.IDFDatabaseManager(settings["physicalDatabase"]).add("PC-99", {})
    commands = iter(
        ["add PC" if launcher is wire else "add-element --kind tray --prefix TR", "exit"]
    )
    monkeypatch.setattr("builtins.input", lambda _: next(commands))
    with patch("lanctl.core.projects.console_session.save_active_project") as save:
        assert (
            launcher.main.__wrapped__(["--database", str(tmp_path / "external.db"), "--cli"]) == 0
        )
    save.assert_not_called()
    assert not saved_inventory(first)["records"]
    assert workspace_is_dirty(settings)


def test_timer_and_close_retain_origin_after_switch_during_edit(workspace, tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor

    first, second = projects(workspace, tmp_path)
    settings = set_mode("automatic.timeToSave")
    session = PhysicalConsoleSession(settings["physicalDatabase"], follow_project=True)
    with session.operation() as path:
        database = wire.IDFDatabaseManager(path)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(activate_project_workspace, second).result(timeout=5)
        database.add("PC-01", {"name": "Original"})
    # B is now dirty too, but this console has never operated on it.
    new_settings = set_mode("automatic.timeToSave")
    wire.IDFDatabaseManager(new_settings["physicalDatabase"]).add("PC-02", {})
    session._deadlines = dict.fromkeys(session._deadlines, 0)
    session._tick()
    assert "PC-01" in saved_inventory(first)["records"]
    assert not saved_inventory(second)["records"]
    assert session.request_close(interactive=False)
    assert not saved_inventory(second)["records"]


def test_timer_retries_and_shuts_down_with_session(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    settings = set_mode("automatic.timeToSave")
    saved = Event()
    calls = 0

    def save(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("temporary disk failure")
        result = save_active_project(*args, **kwargs)
        saved.set()
        return result

    with patch("lanctl.core.projects.console_session.save_active_project", side_effect=save):
        with physical_console_session(settings["physicalDatabase"]) as session:
            with session.operation() as path:
                wire.IDFDatabaseManager(path).add("PC-01", {})
            with physical_console_session(path) as nested:
                assert nested is session
                session.start()
                original_thread = session._thread
                nested.start()
                assert session._thread is original_thread
                session._deadlines = dict.fromkeys(session._deadlines, 0)
                session._tick()
                assert session.messages()
                session._deadlines = dict.fromkeys(session._deadlines, 0)
                assert saved.wait(4)
        assert not session._thread.is_alive()
    assert "PC-01" in saved_inventory(first)["records"]


def test_stop_waits_for_inflight_save(workspace, tmp_path):
    projects(workspace, tmp_path)
    settings = set_mode("automatic.timeToSave")
    session = PhysicalConsoleSession(settings["physicalDatabase"])
    with session.operation():
        pass
    entered, release, stopped = Event(), Event(), Event()

    def save(*args, **kwargs):
        entered.set()
        assert release.wait(4)

    with patch("lanctl.core.projects.console_session.save_active_project", side_effect=save):
        session._deadlines = dict.fromkeys(session._deadlines, 0)
        session.start()
        assert entered.wait(3)
        stopper = Thread(target=lambda: (session.stop(), stopped.set()))
        stopper.start()
        try:
            assert not stopped.wait(0.05)
        finally:
            release.set()
            stopper.join(timeout=4)
        assert stopped.is_set()
        assert not session._thread.is_alive()


def test_invalid_interval_and_config_failure_do_not_kill_worker(workspace, tmp_path):
    from lanctl.core.projects.console_session import _interval

    assert [
        _interval({"projectSaveIntervalMinutes": value})
        for value in ("bad", None, float("inf"), float("nan"))
    ] == [300] * 4
    assert _interval({"projectSaveIntervalMinutes": -1}) == 1
    session = PhysicalConsoleSession(tmp_path / "external.db")
    recovered = Event()
    calls = 0
    original = session._tick

    def tick():
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("config temporarily unavailable")
        original()
        recovered.set()

    with patch.object(session, "_tick", side_effect=tick):
        session.start()
        try:
            assert recovered.wait(4)
        finally:
            session.stop()
    assert session.messages()


def test_wire_tui_invalidates_open_editor_and_handles_cancel(workspace, tmp_path, monkeypatch):
    from lanctl.apps.wire.tui import app as tui

    first, second = projects(workspace, tmp_path)
    settings = set_mode()
    database = wire.IDFDatabaseManager(settings["physicalDatabase"])
    wire.CommandProcessor(database).execute("reserve PC-01 name=First")
    stream = StringIO()
    stream.isatty = lambda: True
    app = tui.LanwireTui(database.path, stream)
    monkeypatch.setattr(app, "render", lambda: None)
    monkeypatch.setattr(tui, "just_fix_windows_console", lambda: None)
    steps = iter(range(5))

    def read(_):
        step = next(steps)
        if step == 0:
            app.view_id = "PC-01"
            app.editor_buffer = "stale edit"
            app.delete_confirmation_id = "PC-01"
            app.command = "delete PC-01"
            activate_project_workspace(second)
            set_mode("manual.inCloseConsult")
            wire.IDFDatabaseManager(load_config()["physicalDatabase"]).add(
                "PC-01", {"name": "Second"}
            )
            return "ENTER"
        if step == 1:
            assert app.view_id is None and app.editor_buffer is None
            assert app.delete_confirmation_id is None and app.command == ""
            assert app.database.path == Path(load_config()["physicalDatabase"])
            return "CTRL_Q"
        if step == 2:
            assert app.running  # cancelled close
            return "ESC"
        pytest.fail("TUI failed to exit")

    answers = iter(["c", "s"])
    monkeypatch.setattr("builtins.input", lambda _: next(answers))
    monkeypatch.setattr(tui, "read_key", read)
    with physical_console_session(database.path, follow_project=True) as session:
        assert app.run() == 0
    assert not session._thread.is_alive()
    assert saved_inventory(first)["records"]["PC-01"]["data"]["name"] == "First"
    assert saved_inventory(second)["records"]["PC-01"]["data"]["name"] == "Second"
    assert stream.getvalue().endswith(tui.LEAVE_SCREEN)
    assert app._console_session is None


@pytest.mark.parametrize("launcher", [wire, rack])
def test_one_shot_reports_failed_close(workspace, tmp_path, monkeypatch, launcher):
    first, _ = projects(workspace, tmp_path)
    set_mode("automatic.toClose")
    args = (
        ["add", "PC"] if launcher is wire else ["add-element", "--kind", "tray", "--prefix", "TR"]
    )
    with patch(
        "lanctl.core.projects.console_session.save_active_project", side_effect=OSError("disk full")
    ):
        assert launcher.main.__wrapped__(args) == 1
    assert workspace_is_dirty(load_config())
    assert not saved_inventory(first)["records"]


@pytest.mark.parametrize("launcher", [wire, rack])
def test_gui_keeps_its_own_lifecycle(workspace, tmp_path, monkeypatch, launcher):
    monkeypatch.setattr(
        PhysicalConsoleSession, "__init__", lambda *_a, **_kw: pytest.fail("GUI console owner")
    )
    with patch("lanctl.apps.suite.launcher_gui.run_gui", return_value=7) as gui:
        assert launcher.main.__wrapped__(["--gui"]) == 7
    gui.assert_called_once_with("lanwire" if launcher is wire else "lanrack", database=None)


@pytest.mark.parametrize("launcher", [wire, rack])
def test_coordinated_console_stops_worker_and_session(workspace, tmp_path, monkeypatch, launcher):
    from lanctl.core.session import current_session

    projects(workspace, tmp_path)
    workers = []
    original = PhysicalConsoleSession.start

    def start(self):
        assert self._owner is current_session()
        assert self._owner.launcher == ("lanwire" if launcher is wire else "lanrack")
        original(self)
        workers.append(self._thread)

    monkeypatch.setattr(PhysicalConsoleSession, "start", start)
    monkeypatch.setattr("builtins.input", lambda _: "exit")
    assert launcher.main(["--cli"]) == 0
    assert len(workers) == 1 and not workers[0].is_alive()
    assert current_session() is None


def test_rack_tui_refreshes_service_and_cancels_close(workspace, tmp_path, monkeypatch):
    first, second = projects(workspace, tmp_path)
    set_mode()
    commands = iter(
        [
            "add-element --kind tray --prefix TR",
            "",
            "add-element --kind tray --prefix PC",
            "",
            "exit",
            "c",
            "exit",
            "s",
        ]
    )
    calls = 0

    def read(_):
        nonlocal calls
        calls += 1
        if calls == 3:
            activate_project_workspace(second)
            set_mode("manual.inCloseConsult")
        return next(commands)

    monkeypatch.setattr("builtins.input", read)
    assert rack.main.__wrapped__(["--tui"]) == 0
    assert len(saved_inventory(first)["records"]) == 1
    assert len(saved_inventory(second)["records"]) == 1


@pytest.mark.parametrize("interrupt", [EOFError, KeyboardInterrupt])
def test_confirmation_interrupt_cancels_without_saving(workspace, tmp_path, interrupt):
    first, _ = projects(workspace, tmp_path)
    settings = set_mode("manual.inCloseConsult")
    session = PhysicalConsoleSession(settings["physicalDatabase"])
    with session.operation() as path:
        wire.IDFDatabaseManager(path).add("PC-01", {})

    def read(_):
        raise interrupt

    assert not session.request_close(input_fn=read)
    assert not session._closed
    assert not saved_inventory(first)["records"]


def test_wire_tui_failure_restores_terminal_and_stops_worker(workspace, tmp_path, monkeypatch):
    from lanctl.apps.wire.tui import app as tui

    projects(workspace, tmp_path)
    stream = StringIO()
    stream.isatty = lambda: True
    app = tui.LanwireTui(load_config()["physicalDatabase"], stream)

    def fail():
        raise OSError("terminal write failed")

    monkeypatch.setattr(app, "render", fail)
    with (
        physical_console_session(app.database.path) as session,
        pytest.raises(OSError, match="terminal write failed"),
    ):
        app.run()
    assert not session._thread.is_alive()
    assert stream.getvalue().endswith(tui.LEAVE_SCREEN)
    assert app._console_session is None


def test_close_does_not_switch_project_during_confirmation(workspace, tmp_path):
    first, second = projects(workspace, tmp_path)
    settings = set_mode("manual.inCloseConsult")
    session = PhysicalConsoleSession(settings["physicalDatabase"], follow_project=True)
    with session.operation() as path:
        wire.IDFDatabaseManager(path).add("PC-01", {})

    def read(_):
        # Explicitly leave the dirty workspace, as another interface can do.
        activate_project_workspace(second, discard_changes=True)
        set_mode("automatic.toClose")
        wire.IDFDatabaseManager(load_config()["physicalDatabase"]).add("PC-02", {})
        return "s"

    assert session.request_close(input_fn=read)
    assert "PC-01" in saved_inventory(first)["records"]
    assert not saved_inventory(second)["records"]
    assert load_config()["activeProject"] == second


def test_explicit_context_preference_save_does_not_reselect_old_project(workspace, tmp_path):
    from lanctl.core.config import save_config

    _, second = projects(workspace, tmp_path)
    session = PhysicalConsoleSession(load_config()["physicalDatabase"])
    with session.operation():
        pass
    activate_project_workspace(second)
    with session.operation():
        settings = load_config()
        settings["startupInterface"] = "cli"
        save_config(settings)
    assert load_config()["activeProject"] == second


def test_nested_different_database_has_its_own_owner(workspace, tmp_path):
    with physical_console_session(tmp_path / "one.db") as first:
        with physical_console_session(tmp_path / "two.db") as second:
            assert first is not second
            with second.operation() as path:
                assert path == tmp_path / "two.db"
        with physical_console_session(tmp_path / "one.db") as reused:
            assert reused is first


def test_empty_notifications_do_not_suspend_tui():
    from lanctl.core.interactive_console import command_console

    with (
        patch("lanctl.core.interactive_console.ManagementScreen") as screen,
        patch("builtins.input", side_effect=["clear", "exit"]),
    ):
        assert command_console("TEST", lambda _: 0, tui=True, notifications=list) == 0
    screen.return_value.__enter__.return_value.suspended.assert_not_called()
