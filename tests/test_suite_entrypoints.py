from unittest.mock import patch

import pytest

from lanctl.bootstrap.lanctl import main
from lanctl.bootstrap.lanmon import main as lanmon_main


def test_orchestrator_routes_ip_to_lanip():
    with patch("lanctl.apps.ip.interfaces.cli.main.main", return_value=7) as application:
        assert main(["ip", "list", "--active"]) == 7
    application.assert_called_once_with(["list", "--active"], program_name="LANIP")


def test_orchestrator_routes_wire_to_lanwire():
    with patch("lanctl.apps.wire.cli.main.main", return_value=8) as application:
        assert main(["wire", "list"]) == 8
    application.assert_called_once_with(["list"])


def test_orchestrator_routes_rack_to_lanrack():
    with patch("lanctl.apps.rack.cli.main", return_value=10) as application:
        assert main(["rack", "--tui"]) == 10
    application.assert_called_once_with(["--tui"])


def test_orchestrator_routes_access_to_lanaccess():
    with patch("lanctl.apps.access.manager_cli.main", return_value=11) as application:
        assert main(["access", "--tui"]) == 11
    application.assert_called_once_with(["--tui"])


def test_unscoped_application_command_is_rejected_by_the_orchestrator():
    with pytest.raises(SystemExit):
        main(["scan", "192.0.2.10"])


def test_lanmon_defaults_to_status_and_forwards_monitor_arguments():
    with patch(
        "lanctl.apps.ip.interfaces.cli.commands.monitor.run_monitor", return_value=4
    ) as application:
        assert lanmon_main([]) == 4
        assert lanmon_main(["list", "--json"]) == 4
    assert application.call_args_list[0].args[0].words == ["status"]
    assert application.call_args_list[1].args[0].words == ["list"]
