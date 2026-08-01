import ipaddress
import unittest
from unittest.mock import patch

from app.services.lan_scanner import LanScanner


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
                "app.services.lan_scanner.active_arp_mac",
                return_value="",
            ),
            patch(
                "app.services.lan_scanner.local_ipv4",
                return_value=ipaddress.IPv4Address("10.0.0.2"),
            ),
        ):
            records = scanner.scan(
                discovery="hybrid", resolve_names=False
            )

        special = {record.alias: record for record in records}
        self.assertEqual(special["GATEWAY"].cnf, "O")
        self.assertEqual(special["BRODCAST"].cnf, "O")


if __name__ == "__main__":
    unittest.main()
