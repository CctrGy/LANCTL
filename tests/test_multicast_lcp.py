import tempfile
import unittest
from pathlib import Path

from app.plugins.manager import PluginManager
from app.plugins.package import build_package, verify_package


class MulticastLcpTests(unittest.TestCase):
    def test_package_activates_and_registers_external_scanner(self):
        source = Path(__file__).resolve().parents[1] / (
            "plugins-src/lanctl.discovery.mdns-ssdp"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "multicast.lcp"
            build_package(source, package)
            verified = verify_package(package)
            self.assertEqual(
                verified["manifest"].plugin_id,
                "lanctl.discovery.mdns-ssdp",
            )
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            plugin = manager.enable(
                "lanctl.discovery.mdns-ssdp",
                grant={
                    "scanner.register",
                    "functions.register",
                    "network.scan",
                },
                trusted=True,
            )
            extensions = manager.extensions.list("scanner")
            self.assertEqual(plugin.state.value, "ENABLED")
            self.assertEqual(extensions[0].specification["methods"], ["mdns", "ssdp"])
            result = manager.functions.call(
                "MdnsSsdp.Network.Discovery.Scan", [], 0.01
            )
            self.assertTrue(result.success)
            self.assertEqual(result.data, {})


if __name__ == "__main__":
    unittest.main()
