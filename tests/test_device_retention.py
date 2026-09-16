import tempfile
import unittest
from pathlib import Path

from lanctl.apps.ip.domain.models import Device
from lanctl.core.device_retention import (
    apply_retention,
    clear_session_devices,
    session_devices,
    with_session_devices,
)


class DeviceRetentionTests(unittest.TestCase):
    def tearDown(self):
        clear_session_devices()

    @staticmethod
    def device(ip, mac, cnf="X", alias=""):
        return Device(ip=ip, mac=mac, cnf=cnf, alias=alias, default_alias=alias)

    def test_permanent_is_the_safe_default(self):
        devices = [self.device("192.168.1.20", "00:11:22:33:44:55")]
        result = apply_retention("devices.json", devices, [False])
        self.assertEqual(len(result.persistent), 1)
        self.assertEqual(len(result.visible), 1)

    def test_forget_unconfirmed_removes_only_disconnected_x(self):
        devices = [
            self.device("192.168.1.20", "00:11:22:33:44:55"),
            self.device("192.168.1.21", "00:11:22:33:44:66", cnf="O"),
            self.device("192.168.1.22", "00:11:22:33:44:77"),
        ]
        result = apply_retention("devices.json", devices, [False, False, True], mode="forget")
        self.assertEqual([item.ip for item in result.persistent], ["192.168.1.21", "192.168.1.22"])
        self.assertEqual([item.ip for item in result.removed], ["192.168.1.20"])

    def test_dhcp_scope_does_not_remove_static_address(self):
        devices = [
            self.device("192.168.1.10", "00:11:22:33:44:55"),
            self.device("192.168.1.50", "00:11:22:33:44:66"),
        ]
        result = apply_retention(
            "devices.json",
            devices,
            [False, False],
            mode="forget",
            scope="dhcp",
            dhcp_range="192.168.1.20-192.168.1.100",
        )
        self.assertEqual([item.ip for item in result.persistent], ["192.168.1.10"])

    def test_reserved_devices_are_always_persistent(self):
        devices = [
            self.device("192.168.1.1", "00:11:22:33:44:55", alias="GATEWAY"),
            self.device("192.168.1.255", "FF:FF:FF:FF:FF:FF", alias="BRODCAST"),
        ]
        result = apply_retention(
            "devices.json", devices, [False, False], mode="forget", target="all"
        )
        self.assertEqual(len(result.persistent), 2)

    def test_session_devices_survive_only_in_process_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "devices.json"
            device = self.device("192.168.1.20", "00:11:22:33:44:55")
            result = apply_retention(path, [device], [False], mode="session")
            self.assertEqual(result.persistent, [])
            self.assertEqual([item.ip for item in session_devices(path)], [device.ip])
            self.assertEqual([item.ip for item in with_session_devices(path, [])], [device.ip])
            clear_session_devices(path)
            self.assertEqual(session_devices(path), [])


if __name__ == "__main__":
    unittest.main()
