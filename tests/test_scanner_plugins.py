import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.plugins.contracts import FunctionResult
from app.plugins.scanners import run_scanner_extensions


class ScannerPluginTests(unittest.TestCase):
    def test_extension_results_are_normalized_and_filtered(self):
        extension = SimpleNamespace(
            extension_id="demo.multicast",
            owner="demo.plugin",
            specification={
                "methods": ["mdns", "ssdp"],
                "function": "Demo.Network.Discovery.Scan",
            },
        )
        manager = SimpleNamespace(
            extensions=SimpleNamespace(list=lambda kind: [extension]),
            functions=SimpleNamespace(call=lambda *args, **kwargs: FunctionResult(
                True,
                data={
                    "192.168.1.20": ["mdns", "inventado"],
                    "no-es-ip": ["ssdp"],
                },
            )),
            audit=lambda *args: None,
        )
        with patch("app.plugins.get_plugin_manager", return_value=manager):
            findings = run_scanner_extensions(("mdns",), 0.5)

        self.assertEqual(findings, {"192.168.1.20": {"MDNS"}})

    def test_unrequested_scanner_is_not_called(self):
        calls = []
        extension = SimpleNamespace(
            extension_id="demo.multicast",
            owner="demo.plugin",
            specification={
                "methods": ["mdns", "ssdp"],
                "function": "Demo.Network.Discovery.Scan",
            },
        )
        manager = SimpleNamespace(
            extensions=SimpleNamespace(list=lambda kind: [extension]),
            functions=SimpleNamespace(call=lambda *args, **kwargs: calls.append(args)),
            audit=lambda *args: None,
        )
        with patch("app.plugins.get_plugin_manager", return_value=manager):
            self.assertEqual(run_scanner_extensions(("wsd",), 0.5), {})
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
