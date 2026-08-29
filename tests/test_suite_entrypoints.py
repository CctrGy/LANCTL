from unittest.mock import patch

from lanctl.bootstrap.lanctl import main
from lanctl.bootstrap.landemo import main as landemo_main
from lanctl.bootstrap.lanmon import main as lanmon_main


def test_orchestrator_routes_ip_to_lanip():
    with patch("lanctl.apps.ip.interfaces.cli.main.main", return_value=7) as application:
        assert main(["ip", "list", "--active"]) == 7
    application.assert_called_once_with(["list", "--active"])


def test_orchestrator_routes_wire_to_lanwire():
    with patch("lanctl.apps.wire.cli.main.main", return_value=8) as application:
        assert main(["wire", "list"]) == 8
    application.assert_called_once_with(["list"])


def test_legacy_commands_are_delegated_to_lanip():
    with patch("lanctl.apps.ip.interfaces.cli.main.main", return_value=9) as application:
        assert main(["scan", "192.0.2.10"]) == 9
    application.assert_called_once_with(["scan", "192.0.2.10"])


def test_lanmon_defaults_to_status_and_forwards_monitor_arguments():
    with patch("lanctl.bootstrap.lanmon.lanctl_main", return_value=4) as application:
        assert lanmon_main([]) == 4
        assert lanmon_main(["list", "--json"]) == 4
    assert application.call_args_list[0].args == (["monitor", "status"],)
    assert application.call_args_list[1].args == (["monitor", "list", "--json"],)


def test_landemo_forwards_to_the_reproducible_demo_command():
    with patch("lanctl.bootstrap.landemo.lanctl_main", return_value=5) as application:
        assert landemo_main(["--output", "presentation", "--force"]) == 5
    application.assert_called_once_with(["demo", "--output", "presentation", "--force"])
