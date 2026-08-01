import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.database import DeviceDatabase
from app.core.recurrent_elements import RecurrentElementDatabase


class RecurrentElementDatabaseTests(unittest.TestCase):
    def test_catalog_recovers_vm1_identity_without_old_ip(self):
        vm1 = next(
            device for device in RecurrentElementDatabase().load()
            if device.alias == "VM1"
        )
        self.assertEqual(vm1.mac, "5E:8C:B3:08:05:D4")
        self.assertEqual(vm1.ip, "-")
        self.assertEqual(vm1.name, "MobilVicttor1")

    def test_scan_recognizes_known_mac_on_any_network(self):
        catalog = [{
            "IP": "-", "cnf": "O", "ALIAS": "MV1",
            "MAC": "5E:8C:B3:08:05:D4", "NAME": "Mi móvil",
            "GROUP": ["VIC"], "description": "Recurrente",
        }]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resource = root / "known.json"
            database_path = root / "devices.json"
            resource.write_text(json.dumps(catalog), encoding="utf-8")
            with patch("app.core.recurrent_elements.bundled_path", return_value=resource):
                device = DeviceDatabase(str(database_path)).upsert([{
                    "IP": "10.20.30.40", "MAC": "5e-8c-b3-08-05-d4"
                }])[0]

        self.assertEqual(device.ip, "10.20.30.40")
        self.assertEqual(device.alias, "MV1")
        self.assertEqual(device.name, "Mi móvil")
        self.assertEqual(device.groups, ["VIC"])
        self.assertEqual(device.cnf, "O")

    def test_existing_user_alias_wins_over_catalog(self):
        catalog = [{
            "IP": "-", "cnf": "O", "ALIAS": "VM1",
            "MAC": "5E:8C:B3:08:05:D4", "NAME": "Mobil-Vic",
        }]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resource = root / "known.json"
            database_path = root / "devices.json"
            resource.write_text(json.dumps(catalog), encoding="utf-8")
            with patch("app.core.recurrent_elements.bundled_path", return_value=resource):
                database = DeviceDatabase(str(database_path))
                database.upsert([{
                    "IP": "192.168.1.39", "MAC": "5E:8C:B3:08:05:D4"
                }])
                database.set_alias("VM1", "TELEFONO")
                rescanned = database.upsert([{
                    "IP": "172.16.0.8", "MAC": "5E:8C:B3:08:05:D4"
                }])[0]

        self.assertEqual(rescanned.alias, "TELEFONO")
        self.assertEqual(rescanned.ip, "172.16.0.8")


if __name__ == "__main__":
    unittest.main()
