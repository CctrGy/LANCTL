import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.commands.ping import run_ping


class PingCommandTests(unittest.TestCase):
    def _args(self, method="auto"):
        return SimpleNamespace(
            selector="ESP",
            method=method,
            timeout=0.5,
            json=False,
            database="devices.json",
        )

    def test_auto_reports_device_found_by_arp_when_ping_is_blocked(self):
        device = SimpleNamespace(ip="192.168.1.44", mac="DE:AD:BE:EF:FE:ED")
        with (
            patch("app.commands.ping.DeviceDatabase") as database,
            patch("app.commands.ping.ping_details", return_value=(False, None, None)),
            patch("app.commands.ping.active_arp_mac", return_value="DE:AD:BE:EF:FE:ED"),
            patch("app.commands.ping.write_log"),
        ):
            database.return_value.resolve.return_value = device
            self.assertEqual(run_ping(self._args()), 0)

    def test_ping_only_does_not_send_active_arp(self):
        device = SimpleNamespace(ip="192.168.1.44", mac="DE:AD:BE:EF:FE:ED")
        with (
            patch("app.commands.ping.DeviceDatabase") as database,
            patch("app.commands.ping.ping_details", return_value=(True, 2.0, 64)),
            patch("app.commands.ping.observed_arp_mac", return_value=""),
            patch("app.commands.ping.active_arp_mac") as active_arp,
            patch("app.commands.ping.write_log"),
        ):
            database.return_value.resolve.return_value = device
            self.assertEqual(run_ping(self._args("ping")), 0)
            active_arp.assert_not_called()


if __name__ == "__main__":
    unittest.main()
