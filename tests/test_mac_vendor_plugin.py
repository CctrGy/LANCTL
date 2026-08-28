import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from lanctl.apps.ip.infrastructure.services.manufacturer import detect_manufacturer
from lanctl.core.plugins.device_adapters import resolve_manufacturer_extensions
from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.package import build_package, verify_package


class MacVendorPluginTests(unittest.TestCase):
    @staticmethod
    def _signed_package(source: Path, root: Path) -> Path:
        key = root / "publisher.pem"
        key.write_bytes(
            Ed25519PrivateKey.generate().private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption(),
            )
        )
        package = root / "mac-vendor.lcp"
        build_package(source, package, signing_key=key)
        return package

    def test_core_manufacturer_detection_prefers_active_adapter(self):
        with patch(
            "lanctl.core.plugins.device_adapters.resolve_manufacturer_extensions",
            return_value="Fabricante del plugin",
        ):
            self.assertEqual(
                detect_manufacturer("00:11:22:33:44:55"),
                "Fabricante del plugin",
            )

    def test_plugin_resolves_bundled_and_custom_longest_prefixes(self):
        source = Path(__file__).resolve().parents[1] / ("plugins-src/lanctl.analysis.mac-vendor")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._signed_package(source, root)
            verified = verify_package(package)
            self.assertEqual(
                verified["manifest"].plugin_id,
                "lanctl.analysis.mac-vendor",
            )
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            manager.publishers.trust_package(package)
            plugin = manager.enable(
                "lanctl.analysis.mac-vendor",
                grant={
                    "command.register",
                    "device-adapter.register",
                    "functions.register",
                    "config.write",
                    "network.http",
                },
                trusted=True,
            )

            self.assertEqual(
                resolve_manufacturer_extensions("00:0C:29:12:34:56", manager),
                "VMware, Inc.",
            )
            added = manager.functions.call(
                "MacVendor.Database.Command",
                ["add", "00:0C:29:12:34:56", "Equipo de laboratorio"],
            )
            self.assertTrue(added.success)
            self.assertEqual(
                resolve_manufacturer_extensions("00:0C:29:12:34:56", manager),
                "Equipo de laboratorio",
            )
            self.assertEqual(plugin.state.value, "ENABLED")

    def test_invalid_prefix_is_rejected_without_changing_database(self):
        source = Path(__file__).resolve().parents[1] / ("plugins-src/lanctl.analysis.mac-vendor")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = self._signed_package(source, root)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            manager.publishers.trust_package(package)
            manager.enable(
                "lanctl.analysis.mac-vendor",
                grant={
                    "command.register",
                    "device-adapter.register",
                    "functions.register",
                    "config.write",
                    "network.http",
                },
                trusted=True,
            )
            with self.assertRaises(ValueError):
                manager.functions.call("MacVendor.Database.Command", ["add", "0011", "Inválido"])


if __name__ == "__main__":
    unittest.main()
