from unittest.mock import patch

from lanctl.bootstrap.lanctl import main


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
