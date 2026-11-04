"""P119: resolve implicit startup before session registration and routing."""

from unittest.mock import Mock

import pytest

from lanctl.core import session

LAUNCHERS = ("lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon")


@pytest.fixture
def startup(monkeypatch):
    config = {}
    monkeypatch.setattr("lanctl.core.config.load_config", lambda: config)
    monkeypatch.setattr("lanctl.core.session_context.consume_context", lambda _, cfg: cfg)
    monkeypatch.setattr("lanctl.core.window_icons.apply_terminal_icon", lambda _: None)
    monkeypatch.setattr(session, "_current", None)
    created = Mock()
    created.return_value.id = "test-session"
    monkeypatch.setattr(session, "Session", created)
    instance = Mock()
    instance.return_value.__enter__ = Mock(return_value=True)
    instance.return_value.__exit__ = Mock(return_value=False)
    monkeypatch.setattr("lanctl.core.gui_instance.GuiInstance", instance)
    return config, created, instance


@pytest.mark.parametrize("launcher", LAUNCHERS)
@pytest.mark.parametrize("preferred", ("cli", "tui", "gui", None, "invalid"))
@pytest.mark.parametrize("routed", (False, True))
def test_implicit_startup_and_registered_mode(startup, launcher, preferred, routed):
    config, created, _ = startup
    if preferred is not None:
        config["startupInterface"] = preferred
    target = Mock(return_value=0)
    entry = session.coordinated_launcher(launcher)(target)
    if routed and launcher != "lanctl":
        route = session.coordinated_launcher("lanctl")(lambda argv: entry(argv[1:]))
        assert route([launcher]) == 0
    else:
        assert entry([]) == 0
    expected = preferred if preferred in {"cli", "tui", "gui"} else "cli"
    assert target.call_args.args[0] == [f"--{expected}"]
    assert created.call_count == 1
    assert created.call_args.args[:2] == (launcher, expected)
    created.return_value.close.assert_called_once()
    assert session.current_session() is None


@pytest.mark.parametrize("launcher", LAUNCHERS)
@pytest.mark.parametrize("arguments", (["--cli"], ["--tui"], ["--gui"], ["status"], ["foreground"]))
def test_explicit_invocations_override_preference(startup, launcher, arguments):
    config, created, _ = startup
    config["startupInterface"] = "gui"
    target = Mock(return_value=0)
    assert session.coordinated_launcher(launcher)(target)(arguments) == 0
    assert target.call_args.args[0] == arguments
    expected = {"--gui": "gui", "--tui": "tui", "foreground": "backend"}.get(arguments[0], "cli")
    assert created.call_args.args[1] == expected


@pytest.mark.parametrize("launcher", LAUNCHERS)
@pytest.mark.parametrize("arguments", (["--help"], ["--version"], ["ephemeral"]))
def test_noninteractive_bypass_does_not_read_configuration(
    startup, monkeypatch, launcher, arguments
):
    _, created, _ = startup
    read = Mock(side_effect=AssertionError("configuration must not be read"))
    monkeypatch.setattr("lanctl.core.config.load_config", read)
    target = Mock(return_value=0)
    assert session.coordinated_launcher(launcher)(target)(arguments) == 0
    created.assert_not_called()
    read.assert_not_called()


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_reentry_preserves_existing_session(startup, monkeypatch, launcher):
    _, created, _ = startup
    parent = Mock(launcher=launcher)
    monkeypatch.setattr(session, "_current", parent)
    target = Mock(return_value=0)
    assert session.coordinated_launcher(launcher)(target)([]) == 0
    assert target.call_args.args[0] == []
    assert session.current_session() is parent
    created.assert_not_called()


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_executable_arguments_and_existing_gui_are_reused(startup, monkeypatch, launcher):
    config, created, instance = startup
    config["startupInterface"] = "gui"
    monkeypatch.setattr("sys.argv", [launcher])
    instance.return_value.__enter__.return_value = False
    target = Mock()
    assert session.coordinated_launcher(launcher)(target)() == 0
    instance.assert_called_once_with(launcher)
    created.assert_not_called()
    target.assert_not_called()
    instance.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("launcher", LAUNCHERS)
def test_config_failure_keeps_origin_and_does_not_start_interface(startup, monkeypatch, launcher):
    _, created, _ = startup
    monkeypatch.setattr(
        "lanctl.core.config.load_config", Mock(side_effect=PermissionError("denied"))
    )
    report = Mock()
    monkeypatch.setattr("lanctl.core.errors.errors.from_exception", report)
    target = Mock()
    assert session.coordinated_launcher(launcher)(target)([]) == 2
    assert report.call_args.kwargs["origin"] == "LANCTL.Core.Coordination.Startup"
    target.assert_not_called()
    created.assert_not_called()
