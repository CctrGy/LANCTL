import io
import unittest

from app.commands.open import connection_target
from app.core.output import render_records
from app.core.progress import ScanProgress
from app.core.query import matches_query
from app.models import Device
from app.services.network_discovery import discovery_probe
from app.services.scan_profiles import apply_profile


class _Tty(io.StringIO):
    def isatty(self):
        return True


class ExtensionTests(unittest.TestCase):
    def test_scan_profiles_apply_distinct_tradeoffs(self):
        fast, fast_timeout, fast_workers = apply_profile("fast", 1.0, 64)
        accurate, accurate_timeout, accurate_workers = apply_profile("accurate", 1.0, 64)
        self.assertEqual(fast.discovery, "arp")
        self.assertLess(fast_timeout, accurate_timeout)
        self.assertGreater(fast_workers, accurate_workers)
        self.assertIn("wsd", accurate.extra_methods)

    def test_discovery_probes_use_standard_multicast_endpoints(self):
        self.assertEqual(discovery_probe("ssdp")[1], ("239.255.255.250", 1900))
        self.assertEqual(discovery_probe("mdns")[1], ("224.0.0.251", 5353))
        self.assertEqual(discovery_probe("wsd")[1], ("239.255.255.250", 3702))

    def test_progress_is_machine_silent_and_tty_visible(self):
        silent = io.StringIO()
        progress = ScanProgress(True, silent)
        progress.start("ARP", 2)
        progress.advance()
        progress.finish()
        self.assertEqual(silent.getvalue(), "")

        tty = _Tty()
        progress = ScanProgress(True, tty)
        progress.start("ARP", 2)
        progress.advance()
        progress.finish()
        self.assertIn("100.0%", tty.getvalue())

    def test_expressive_queries_are_combined_without_eval(self):
        device = Device(
            ip="192.168.1.18", mac="10:20:30:40:50:60", cnf="O",
            groups=["IOT"], manufacturer="Hunan Fn-Link",
        )
        self.assertTrue(matches_query(device, True, "active and group=IOT and vendor~fn-link"))
        self.assertFalse(matches_query(device, False, "active and group=IOT"))
        with self.assertRaises(ValueError):
            matches_query(device, True, "__import__('os')")

    def test_html_and_xml_exports_escape_values(self):
        record = {"IP": "192.168.1.1", "ALIAS": "A&B"}
        html = render_records([record], "html", columns=["ip", "alias"])
        xml = render_records([record], "xml", columns=["ip", "alias"])
        self.assertIn("A&amp;B", html)
        self.assertIn("A&amp;B", xml)

    def test_connection_targets_are_protocol_consistent(self):
        self.assertEqual(connection_target("192.168.1.10", "https", 8443), "https://192.168.1.10:8443/")
        self.assertEqual(connection_target("192.168.1.11", "smb", path="share"), r"\\192.168.1.11\share")
        self.assertEqual(connection_target("192.168.1.31", "rdp"), "192.168.1.31:3389")


if __name__ == "__main__":
    unittest.main()
