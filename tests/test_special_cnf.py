import ipaddress
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from lanctl.apps.ip.domain.models import Device
from lanctl.apps.ip.infrastructure.services.lan_scanner import LanScanner
from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.vlf import create_project


class SpecialElementCnfTests(unittest.TestCase):
    def test_gateway_and_broadcast_default_to_ok(self):
        scanner = LanScanner(
            ipaddress.IPv4Network("192.168.50.0/30"),
            workers=2,
            timeout=0.05,
            max_hosts=4,
        )
        with (
            patch.object(scanner, "_ping", return_value=False),
            patch.object(scanner, "_read_arp_table", return_value={}),
            patch.object(scanner, "_local_mac", return_value=""),
            patch.object(scanner, "_resolve_name", return_value=""),
            patch(
                "lanctl.apps.ip.infrastructure.services.lan_scanner.active_arp_mac",
                return_value="",
            ),
            patch(
                "lanctl.apps.ip.infrastructure.services.lan_scanner.local_ipv4",
                return_value=ipaddress.IPv4Address("10.0.0.2"),
            ),
        ):
            records = scanner.scan(discovery="hybrid", resolve_names=False)

        special = {record.alias: record for record in records}
        self.assertEqual(special["GATEWAY"].cnf, "O")
        self.assertEqual(special["BRODCAST"].cnf, "O")

    def test_gateway_detected_as_normal_host_is_promoted_to_ok(self):
        scanner = LanScanner(
            ipaddress.IPv4Network("192.168.50.0/24"),
            workers=2,
            timeout=0.05,
            max_hosts=256,
        )
        ordinary = Device(ip="192.168.50.1", mac="10:20:30:40:50:60", cnf="X")

        records = scanner._include_special_devices([ordinary], {ordinary.ip: ordinary.mac})

        gateway = next(record for record in records if record.alias == "GATEWAY")
        self.assertEqual(gateway.cnf, "O")

    def test_reserved_gateway_repairs_previous_unknown_state(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temporary:
            path = f"{temporary}/devices.json"
            database = DeviceDatabase(path)
            database.upsert(
                [
                    {
                        "IP": "192.168.50.1",
                        "MAC": "10:20:30:40:50:60",
                        "cnf": "X",
                    }
                ]
            )

            gateway = database.upsert(
                [
                    {
                        "IP": "192.168.50.1",
                        "MAC": "10:20:30:40:50:60",
                        "cnf": "O",
                        "ALIAS": "GATEWAY",
                        "defaultAlias": "GATEWAY",
                    }
                ]
            )[0]

            self.assertEqual(gateway.cnf, "O")

    def test_reserved_defaults_are_repaired_when_loading_legacy_data(self):
        device = Device.from_dict(
            {
                "IP": "192.168.50.1",
                "MAC": "10:20:30:40:50:60",
                "cnf": "X",
                "ALIAS": "GATEWAY",
                "defaultAlias": "GATEWAY",
                "GROUP": [],
                "description": "-",
            }
        )

        self.assertEqual(device.cnf, "O")
        self.assertEqual(device.alias, "GATEWAY")
        self.assertIn("BASIC", device.groups)
        self.assertEqual(device.description, "Puerta de enlace de la red")

    def test_reserved_role_updates_instead_of_creating_a_duplicate(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temporary:
            database = DeviceDatabase(f"{temporary}/devices.json")
            database.upsert(
                [
                    {
                        "IP": "192.168.1.1",
                        "MAC": "10:20:30:40:50:60",
                        "ALIAS": "GATEWAY",
                        "defaultAlias": "GATEWAY",
                    }
                ]
            )

            devices = database.upsert(
                [
                    {
                        "IP": "10.0.0.1",
                        "MAC": "AA:BB:CC:DD:EE:FF",
                        "ALIAS": "GATEWAY",
                        "defaultAlias": "GATEWAY",
                    }
                ]
            )

            gateways = [device for device in devices if device.default_alias == "GATEWAY"]
            self.assertEqual(len(gateways), 1)
            self.assertEqual(gateways[0].ip, "10.0.0.1")
            self.assertEqual(gateways[0].mac, "AA:BB:CC:DD:EE:FF")
            self.assertEqual(gateways[0].cnf, "O")

    def test_new_project_contains_both_reserved_elements_as_ok(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = f"{temporary}/devices.json"
            groups = f"{temporary}/groups.json"
            project = f"{temporary}/home.vlf"
            create_project(
                project,
                config={
                    "database": database,
                    "groups": groups,
                    "range": "10.20.30.0/24",
                    "gateway": "10.20.30.254",
                },
            )
            with ZipFile(project) as archive:
                sqlite_path = f"{temporary}/elements.db"
                with open(sqlite_path, "wb") as stream:
                    stream.write(archive.read("devices/elements.db"))
            connection = sqlite3.connect(sqlite_path)
            try:
                payloads = [
                    json.loads(row[0]) for row in connection.execute("SELECT raw_json FROM devices")
                ]
            finally:
                connection.close()

            reserved = {item["defaultAlias"]: item for item in payloads}
            self.assertEqual(reserved["GATEWAY"]["IP"], "10.20.30.254")
            self.assertEqual(reserved["GATEWAY"]["cnf"], "O")
            self.assertEqual(reserved["BRODCAST"]["IP"], "10.20.30.255")
            self.assertEqual(reserved["BRODCAST"]["cnf"], "O")


if __name__ == "__main__":
    unittest.main()
