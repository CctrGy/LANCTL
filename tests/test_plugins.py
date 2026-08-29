import json
import os
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from lanctl.core.plugins.contracts import EventContract, FunctionResult
from lanctl.core.plugins.events import EventBus, EventRegistry
from lanctl.core.plugins.functions import FunctionRegistry
from lanctl.core.plugins.manager import PluginManager
from lanctl.core.plugins.models import PluginManifest, PluginState
from lanctl.core.plugins.package import build_package, verify_package
from lanctl.core.plugins.publishers import TrustedPublisherStore
from lanctl.core.resources import bundled_path


@dataclass(frozen=True, slots=True)
class DemoEvent(EventContract):
    value: str


class PluginTests(unittest.TestCase):
    def test_official_catalog_matches_verified_bundled_packages(self):
        catalog = json.loads(
            bundled_path("bundled/plugin-catalog.json").read_text(encoding="utf-8")
        )
        self.assertEqual(catalog["schemaVersion"], 1)
        for entry in catalog["plugins"]:
            package = bundled_path("bundled") / entry["package"]
            result = verify_package(package)
            self.assertEqual(result["manifest"].plugin_id, entry["id"])
            self.assertEqual(result["manifest"].version, entry["version"])

    def test_builtin_example_and_developer_readme_are_bootstrapped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = PluginManager(root / "plugins", root / "registry.json")
            example = manager.get("lanctl.example.network-summary")
            self.assertEqual(example.state, PluginState.ENABLED)
            for plugin_id in (
                "lanctl.analysis.mac-vendor",
                "lanctl.discovery.mdns-ssdp",
                "lanctl.discovery.windows-smb",
                "lanctl.network.wol",
            ):
                self.assertEqual(manager.get(plugin_id).state, PluginState.DISABLED)
            self.assertTrue((root / "plugins/readme.md").is_file())
            readme = (root / "plugins/readme.md").read_text(encoding="utf-8")
            self.assertIn("LANCTL.Network.Scan.Begin", readme)
            self.assertIn("inventory.summary", readme)
            manager.activate_enabled()
            commands = manager.extensions.list("command")
            self.assertEqual(commands[0].specification["name"], "network-summary")
            with self.assertRaises(PermissionError):
                manager.uninstall(example.manifest.plugin_id)

    def test_manifest_cannot_self_declare_builtin_or_enable_itself(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            injected = root / "plugins/evil.autostart"
            injected.mkdir(parents=True)
            (injected / "plugin.info").write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "id": "evil.autostart",
                        "name": "Injected",
                        "version": "1.0.0",
                        "entryPoint": "main.exec",
                        "runtime": "isolated",
                        "builtIn": True,
                        "defaultEnabled": True,
                        "permissions": ["network.udp"],
                    }
                ),
                encoding="utf-8",
            )
            manager = PluginManager(root / "plugins", root / "registry.json")
            plugin = manager.get("evil.autostart")
            self.assertEqual(plugin.state, PluginState.DISABLED)
            self.assertEqual(plugin.granted, set())
            self.assertFalse(plugin.manifest.raw["builtIn"])

    def _source(self, root: Path, *, runtime="isolated", permissions=None) -> Path:
        source = root / "source"
        (source / "api").mkdir(parents=True)
        (source / "plugin.info").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "id": "demo.network-tools",
                    "name": "Network Tools",
                    "version": "1.0.0",
                    "entryPoint": "main.exec",
                    "runtime": runtime,
                    "lanctl": {"minimumVersion": "0.3.0", "maximumVersion": "0.x"},
                    "permissions": permissions or ["theme.register"],
                    "capabilities": ["theme", "network"],
                }
            ),
            encoding="utf-8",
        )
        (source / "api/api.map").write_text(
            json.dumps(
                {
                    "extensions": [
                        {
                            "id": "demo.theme.dark",
                            "type": "theme",
                            "specification": {"palette": "dark"},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (source / "main.exec").write_text(
            "def activate(api):\n    api.log('ACTIVATE')\n",
            encoding="utf-8",
        )
        return source

    def test_manifest_rejects_unknown_capability_and_unsafe_entrypoint(self):
        base = {"id": "demo.valid", "capabilities": ["unknown"]}
        with self.assertRaises(ValueError):
            PluginManifest.from_dict(base)
        with self.assertRaises(ValueError):
            PluginManifest.from_dict({"id": "demo.valid", "entryPoint": "../main.py"})
        with self.assertRaisesRegex(ValueError, "schema LCP no compatible"):
            PluginManifest.from_dict(
                {
                    "schemaVersion": 2,
                    "id": "demo.valid",
                    "capabilities": ["plugin"],
                }
            )

    def test_package_build_verify_install_and_declarative_enable(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "network-tools.lcp"
            built = build_package(self._source(root), package)
            self.assertTrue(built["valid"])
            self.assertEqual(verify_package(package)["manifest"].plugin_id, "demo.network-tools")
            manager = PluginManager(root / "installed", root / "registry.json")
            plugin = manager.install(package)
            self.assertEqual(plugin.state, PluginState.DISABLED)
            with self.assertRaises(PermissionError):
                manager.enable(plugin.manifest.plugin_id)
            manager.enable(plugin.manifest.plugin_id, grant={"theme.register"})
            active = manager.get(plugin.manifest.plugin_id)
            self.assertEqual(active.state, PluginState.ENABLED)
            self.assertIsNotNone(active.isolated_runtime)
            self.assertNotEqual(active.isolated_runtime.pid, os.getpid())
            self.assertTrue(active.isolated_runtime.process.is_alive())
            self.assertEqual(manager.extensions.list("theme")[0].extension_id, "demo.theme.dark")
            manager.disable(plugin.manifest.plugin_id)
            self.assertEqual(manager.extensions.list(), [])

    def test_signed_package_and_permission_revocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key = root / "publisher.pem"
            key.write_bytes(
                Ed25519PrivateKey.generate().private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            package = root / "signed.lcp"
            result = build_package(self._source(root), package, signing_key=key)
            self.assertTrue(result["signature"].startswith("VALID_ED25519:"))

            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            manager.enable("demo.network-tools", grant={"theme.register"})
            plugin = manager.revoke("demo.network-tools", {"theme.register"})
            self.assertEqual(plugin.state, PluginState.DISABLED)
            self.assertEqual(plugin.granted, set())
            with self.assertRaises(PermissionError):
                manager.enable("demo.network-tools")

    def test_trusted_runtime_requires_explicit_trust(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key = root / "publisher.pem"
            key.write_bytes(
                Ed25519PrivateKey.generate().private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            package = root / "trusted.lcp"
            build_package(self._source(root, runtime="trusted"), package, signing_key=key)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            with self.assertRaises(PermissionError):
                manager.enable("demo.network-tools", grant={"theme.register"})
            with self.assertRaisesRegex(PermissionError, "editor confiable"):
                manager.enable("demo.network-tools", grant={"theme.register"}, trusted=True)
            manager.publishers.trust_package(package)
            plugin = manager.enable("demo.network-tools", grant={"theme.register"}, trusted=True)
            self.assertIsNotNone(plugin.module)
            fingerprint = plugin.signature.split(":", 1)[1]
            self.assertTrue(manager.publishers.revoke(fingerprint))
            reloaded = PluginManager(root / "installed", root / "registry.json")
            reloaded.activate_enabled()
            self.assertEqual(reloaded.get("demo.network-tools").state, PluginState.ERROR)

    def test_signed_publisher_can_be_trusted_and_revoked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key = root / "publisher.pem"
            key.write_bytes(
                Ed25519PrivateKey.generate().private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            package = root / "signed.lcp"
            result = build_package(self._source(root), package, signing_key=key)
            store = TrustedPublisherStore(root / "publishers.json")
            entry = store.trust_package(package, "Demo Publisher")
            self.assertTrue(store.is_trusted(result["signature"]))
            self.assertEqual(store.list()[0]["name"], "Demo Publisher")
            self.assertTrue(store.revoke(entry["fingerprint"]))
            self.assertFalse(store.list())

    def test_unsigned_package_cannot_become_trusted_publisher(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "unsigned.lcp"
            build_package(self._source(root), package)
            with self.assertRaisesRegex(ValueError, "firmado válido"):
                TrustedPublisherStore(root / "publishers.json").trust_package(package)

    def test_isolated_runtime_enforces_call_budget(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root)
            manifest = json.loads((source / "plugin.info").read_text(encoding="utf-8"))
            manifest["limits"] = {"timeoutSeconds": 0.2, "memoryMb": 64, "maxCalls": 1}
            (source / "plugin.info").write_text(json.dumps(manifest), encoding="utf-8")
            (source / "main.exec").write_text(
                "def activate(api):\n    api.log('one')\n    api.log('two')\n",
                encoding="utf-8",
            )
            package = root / "limited.lcp"
            build_package(source, package)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            with self.assertRaisesRegex(RuntimeError, "límite de llamadas"):
                manager.enable("demo.network-tools", grant={"theme.register"})
            self.assertEqual(manager.get("demo.network-tools").state, PluginState.BLOCKED)

    def test_trusted_declared_hook_is_connected_to_event_bus(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(
                root, runtime="trusted", permissions=["theme.register", "events.listen"]
            )
            hooks = source / "api/hooks"
            hooks.mkdir()
            (hooks / "startup.hook").write_text(
                json.dumps({"event": "LANCTL.Core.Lifecycle.Startup", "handler": "on_startup"}),
                encoding="utf-8",
            )
            (source / "main.exec").write_text(
                "CALLED = []\n"
                "def on_startup(event):\n    CALLED.append(event.mode)\n"
                "def activate(api):\n    pass\n",
                encoding="utf-8",
            )
            package = root / "hooks.lcp"
            key = root / "publisher.pem"
            key.write_bytes(
                Ed25519PrivateKey.generate().private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            build_package(source, package, signing_key=key)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            manager.publishers.trust_package(package)
            plugin = manager.enable(
                "demo.network-tools", grant={"theme.register", "events.listen"}, trusted=True
            )
            manager.events.emit(
                "LANCTL.Core.Lifecycle.Startup", {"version": "test", "mode": "unit"}
            )
            self.assertEqual(plugin.module.CALLED, ["unit"])

    def test_event_bus_uses_contract_and_isolates_plugin_errors(self):
        audit = []
        registry = EventRegistry()
        registry.register("Demo.Network.Scan.Begin", DemoEvent, owner="demo")
        bus = EventBus(registry, lambda *parts: audit.append(parts))
        received = []
        bus.subscribe(
            "Demo.Network.Scan.Begin",
            lambda event: received.append(event.value),
            plugin_id="demo.good",
        )
        bus.subscribe("Demo.Network.Scan.Begin", lambda event: 1 / 0, plugin_id="demo.bad")
        event = bus.emit("Demo.Network.Scan.Begin", {"value": "ok"}, source="demo")
        self.assertEqual(event.value, "ok")
        self.assertEqual(received, ["ok"])
        self.assertTrue(any(parts[3] == "ERROR" for parts in audit))

    def test_plugins_cannot_register_core_namespace(self):
        registry = EventRegistry()
        with self.assertRaises(PermissionError):
            registry.register("LANCTL.Network.Scan.Custom", DemoEvent, owner="demo")

    def test_declarative_event_schema_builds_a_typed_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, permissions=["theme.register", "events.register"])
            (source / "api/events.schema").write_text(
                json.dumps(
                    {
                        "events": {
                            "Demo.Network.Scan.Begin": {
                                "arguments": {"scan_id": "string", "target": "string?"}
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            package = root / "events.lcp"
            build_package(source, package)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            manager.enable("demo.network-tools", grant={"theme.register", "events.register"})
            event = manager.events.emit(
                "Demo.Network.Scan.Begin", {"scan_id": "abc"}, source="demo.network-tools"
            )
            self.assertEqual(event.scan_id, "abc")
            self.assertIsNone(event.target)
            self.assertIsInstance(event, EventContract)

    def test_function_registry_requires_the_declared_return_contract(self):
        registry = FunctionRegistry()
        registry.register(
            "Demo.Core.Action.Run", lambda: FunctionResult(True), FunctionResult, owner="demo"
        )
        self.assertTrue(registry.call("Demo.Core.Action.Run", caller="test").success)
        registry.register("Demo.Core.Action.Bad", dict, FunctionResult, owner="demo")
        with self.assertRaises(TypeError):
            registry.call("Demo.Core.Action.Bad", caller="test")


if __name__ == "__main__":
    unittest.main()
