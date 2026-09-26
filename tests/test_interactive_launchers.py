from unittest.mock import Mock, patch

import pytest

from lanctl.bootstrap.lanctl import main
from lanctl.core.interactive_console import command_console


@pytest.mark.parametrize(
    "flag,tui", [("--cli", False), ("-cli", False), ("--tui", True), ("-tui", True)]
)
def test_root_owns_its_console(flag, tui):
    with patch("lanctl.apps.suite.interfaces.run_console", return_value=0) as console:
        assert main([flag]) == 0
    console.assert_called_once_with(tui=tui)


def test_root_default_does_not_start_inventory():
    with patch("lanctl.apps.suite.interfaces.run_console", return_value=0) as console:
        assert main([]) == 0
    console.assert_called_once_with(tui=False)


def test_child_help_returns_to_suite(capsys):
    with patch("builtins.input", side_effect=["lanip --help", "version", "exit"]):
        assert main(["--cli"]) == 0
    assert "LANIP" in capsys.readouterr().out


def test_console_preserves_quoted_arguments_and_recovers_parser_errors():
    dispatch = Mock(side_effect=[SystemExit(2), 0])
    with patch("builtins.input", side_effect=['show "rack one"', "help show", "exit"]):
        assert command_console("TEST", dispatch) == 0
    assert dispatch.call_args_list[0].args[0] == ["show", "rack one"]
    assert dispatch.call_args_list[1].args[0] == ["show", "--help"]


def test_tui_suspends_screen_for_child_and_returns():
    dispatch = Mock(return_value=0)
    with (
        patch("lanctl.core.interactive_console.ManagementScreen") as screen,
        patch("builtins.input", side_effect=["1", "", "exit"]),
    ):
        assert command_console("TEST", dispatch, tui=True, shortcuts={"1": ["lanip", "--tui"]}) == 0
    screen.return_value.__enter__.return_value.suspended.assert_called_once()
    dispatch.assert_called_once_with(["lanip", "--tui"])


def test_lanmon_console_dispatches_real_commands():
    from lanctl.bootstrap.lanmon import main as monitor

    with (
        patch("builtins.input", side_effect=["status", "exit"]),
        patch("lanctl.apps.monitor.commands.run_monitor", return_value=0) as command,
    ):
        assert monitor(["--cli"]) == 0
    assert command.call_args.args[0].words == ["status"]


@pytest.mark.parametrize(
    "module",
    [
        "lanctl.bootstrap.lanctl",
        "lanctl.bootstrap.lanmon",
        "lanctl.apps.access.manager_cli",
        "lanctl.apps.rack.cli",
        "lanctl.apps.wire.cli.main",
        "lanctl.apps.ip.interfaces.cli.main",
    ],
)
def test_all_parsers_offer_both_modes(module):
    from importlib import import_module

    parser = import_module(module).build_parser()
    options = {option for action in parser._actions for option in action.option_strings}
    assert {"--cli", "-cli", "--tui", "-tui"} <= options


def test_rack_cli_and_tui_use_same_service():
    from lanctl.apps.rack.cli import run_cli, run_tui

    service = Mock()
    service.list.return_value = []
    with patch("builtins.input", side_effect=["list", "exit"]):
        assert run_cli(service) == 0
    with patch("builtins.input", side_effect=["list", "", "exit"]):
        assert run_tui(service) == 0
    assert service.list.call_count >= 2


def test_child_interrupt_does_not_close_parent():
    dispatch = Mock(side_effect=[KeyboardInterrupt, 0])
    with patch("builtins.input", side_effect=["status", "status", "exit"]):
        assert command_console("TEST", dispatch) == 0
    assert dispatch.call_count == 2


def test_failed_view_keeps_commands_available():
    overview = Mock(side_effect=ValueError("invalid inventory"))
    with (
        patch("builtins.input", return_value="exit"),
        patch("lanctl.core.interactive_console.errors.from_exception") as report,
    ):
        assert command_console("TEST", Mock(), tui=True, overview=overview) == 0
    report.assert_called_once()
