import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lanctl.core.database import DeviceDatabase
from lanctl.core.recurrent_elements import RecurrentElementDatabase


class RecurrentElementDatabaseTests(unittest.TestCase):
    def test_legacy_list_catalog_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / "recurrent.json"
            resource.write_text(
                json.dumps([{"MAC": "5E:8C:B3:08:05:D4", "ALIAS": "VM1"}]),
                encoding="utf-8",
            )
            with patch("lanctl.core.recurrent_elements.application_path", return_value=resource):
                device = RecurrentElementDatabase().load()[0]

        self.assertEqual(device.alias, "VM1")

    def test_versioned_catalog_document_is_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / "recurrent.json"
            resource.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "documentType": "lanctl.recurrent-elements",
                        "elements": [{"MAC": "5E:8C:B3:08:05:D4", "NAME": "Movil"}],
                    }
                ),
                encoding="utf-8",
            )
            with patch("lanctl.core.recurrent_elements.application_path", return_value=resource):
                device = RecurrentElementDatabase().load()[0]
        self.assertEqual(device.name, "Movil")

    def test_catalog_index_is_reused_after_first_load(self):
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / "recurrent.json"
            resource.write_text(
                json.dumps(
                    [
                        {
                            "MAC": "5E:8C:B3:08:05:D4",
                            "NAME": "Movil",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            with patch("lanctl.core.recurrent_elements.application_path", return_value=resource):
                database = RecurrentElementDatabase()
                first = database.find_by_mac("5E:8C:B3:08:05:D4")
                resource.unlink()
                cached = database.find_by_mac("5E:8C:B3:08:05:D4")
        self.assertEqual(first.name, "Movil")
        self.assertEqual(cached.name, "Movil")
        self.assertIsNot(first, cached)

    def test_versioned_catalog_rejects_wrong_document_type_without_erasing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / "recurrent.json"
            payload = {
                "schemaVersion": 1,
                "documentType": "lanctl.other-document",
                "elements": [],
            }
            resource.write_text(json.dumps(payload), encoding="utf-8")
            original = resource.read_bytes()

            with (
                patch("lanctl.core.recurrent_elements.application_path", return_value=resource),
                self.assertRaisesRegex(ValueError, "tipo de documento"),
            ):
                RecurrentElementDatabase().load()

            self.assertEqual(resource.read_bytes(), original)

    def test_versioned_catalog_requires_an_elements_list(self):
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / "recurrent.json"
            resource.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "documentType": "lanctl.recurrent-elements",
                        "elements": {},
                    }
                ),
                encoding="utf-8",
            )
            with (
                patch("lanctl.core.recurrent_elements.application_path", return_value=resource),
                self.assertRaisesRegex(ValueError, "sección elements"),
            ):
                RecurrentElementDatabase().load()

    def test_upsert_reads_the_inventory_only_once(self):
        with tempfile.TemporaryDirectory() as directory:
            database = DeviceDatabase(str(Path(directory) / "devices.json"))
            with patch.object(database, "load", wraps=database.load) as load:
                database.upsert(
                    [
                        {
                            "IP": "192.0.2.10",
                            "MAC": "02:00:00:00:00:10",
                        }
                    ]
                )
        load.assert_called_once_with()

    def test_catalog_recovers_vm1_identity_without_old_ip(self):
        with tempfile.TemporaryDirectory() as directory:
            resource = Path(directory) / "recurrent.json"
            resource.write_text(
                json.dumps(
                    [
                        {
                            "IP": "-",
                            "cnf": "O",
                            "ALIAS": "VM1",
                            "MAC": "5E:8C:B3:08:05:D4",
                            "NAME": "MobilVictor1",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            with patch("lanctl.core.recurrent_elements.application_path", return_value=resource):
                vm1 = RecurrentElementDatabase().load()[0]
        self.assertEqual(vm1.mac, "5E:8C:B3:08:05:D4")
        self.assertEqual(vm1.ip, "-")
        self.assertEqual(vm1.name, "MobilVictor1")

    def test_scan_recognizes_known_mac_on_any_network(self):
        catalog = [
            {
                "IP": "-",
                "cnf": "O",
                "ALIAS": "MV1",
                "MAC": "5E:8C:B3:08:05:D4",
                "NAME": "Mi móvil",
                "GROUP": ["VIC"],
                "description": "Recurrente",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resource = root / "known.json"
            database_path = root / "devices.json"
            resource.write_text(json.dumps(catalog), encoding="utf-8")
            with patch("lanctl.core.recurrent_elements.application_path", return_value=resource):
                device = DeviceDatabase(str(database_path)).upsert(
                    [{"IP": "10.20.30.40", "MAC": "5e-8c-b3-08-05-d4"}]
                )[0]

        self.assertEqual(device.ip, "10.20.30.40")
        self.assertEqual(device.alias, "MV1")
        self.assertEqual(device.name, "Mi móvil")
        self.assertEqual(device.groups, ["VIC"])
        self.assertEqual(device.cnf, "O")

    def test_existing_user_alias_wins_over_catalog(self):
        catalog = [
            {
                "IP": "-",
                "cnf": "O",
                "ALIAS": "VM1",
                "MAC": "5E:8C:B3:08:05:D4",
                "NAME": "Mobil-Vic",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            resource = root / "known.json"
            database_path = root / "devices.json"
            resource.write_text(json.dumps(catalog), encoding="utf-8")
            with patch("lanctl.core.recurrent_elements.application_path", return_value=resource):
                database = DeviceDatabase(str(database_path))
                database.upsert([{"IP": "192.168.1.39", "MAC": "5E:8C:B3:08:05:D4"}])
                database.set_alias("VM1", "TELEFONO")
                rescanned = database.upsert([{"IP": "172.16.0.8", "MAC": "5E:8C:B3:08:05:D4"}])[0]

        self.assertEqual(rescanned.alias, "TELEFONO")
        self.assertEqual(rescanned.ip, "172.16.0.8")


if __name__ == "__main__":
    unittest.main()
