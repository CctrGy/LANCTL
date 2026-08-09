import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.cli import build_parser
from app.core.database import DeviceDatabase
from app.models import normalize_cnf
from app.tui import LanctlTui


class FixedCnfTests(unittest.TestCase):
    def test_f_is_a_valid_cnf_state(self):
        self.assertEqual(normalize_cnf("F"), "F")
        self.assertEqual(normalize_cnf("fixed"), "F")
        self.assertEqual(normalize_cnf("fijo"), "F")

    def test_cnf_without_value_releases_fixed_state_to_ok(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "devices.json"
            database = DeviceDatabase(str(path))
            device = database.add_device("AA:BB:CC:DD:EE:FF", alias="PORTATIL")
            fixed = build_parser().parse_args(["cnf", device.mac, "F", "--database", str(path)])
            fixed.handler(fixed)
            self.assertEqual(database.resolve(device.mac).cnf, "F")

            released = build_parser().parse_args(["cnf", device.mac, "--database", str(path)])
            released.handler(released)
            self.assertEqual(database.resolve(device.mac).cnf, "O")

    def test_cnf_without_value_keeps_a_non_fixed_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "devices.json"
            database = DeviceDatabase(str(path))
            device = database.add_device("AA:BB:CC:DD:EE:FF")
            args = build_parser().parse_args(["cnf", device.mac, "--database", str(path)])
            args.handler(args)
            self.assertEqual(database.resolve(device.mac).cnf, "X")

    def test_tui_arrows_cannot_move_a_fixed_selection(self):
        tui = object.__new__(LanctlTui)
        tui.devices = [
            SimpleNamespace(cnf="F", alias="FIJO", name="", ip="192.168.1.2"),
            SimpleNamespace(cnf="O", alias="OTRO", name="", ip="192.168.1.3"),
        ]
        tui.index = 0
        tui.messages = []

        tui.move(1)
        self.assertEqual(tui.index, 0)
        self.assertIn("Selección fijada", tui.messages[0])

        tui.devices[0].cnf = "O"
        tui.move(1)
        self.assertEqual(tui.index, 1)


if __name__ == "__main__":
    unittest.main()
