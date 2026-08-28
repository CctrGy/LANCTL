import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.package import build_package, verify_package


class MulticastLcpTests(unittest.TestCase):
    def test_package_activates_and_registers_external_scanner(self):
        source = Path(__file__).resolve().parents[1] / ("plugins-src/lanctl.discovery.mdns-ssdp")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            key = root / "publisher.pem"
            key.write_bytes(
                Ed25519PrivateKey.generate().private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            package = root / "multicast.lcp"
            build_package(source, package, signing_key=key)
            verified = verify_package(package)
            self.assertEqual(
                verified["manifest"].plugin_id,
                "lanctl.discovery.mdns-ssdp",
            )
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            manager.publishers.trust_package(package)
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
            result = manager.functions.call("MdnsSsdp.Network.Discovery.Scan", [], 0.01)
            self.assertTrue(result.success)
            self.assertEqual(result.data, {})


if __name__ == "__main__":
    unittest.main()
