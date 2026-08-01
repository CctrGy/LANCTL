import json
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from app.plugins.contracts import EventContract, EventMetadata
from app.plugins.contracts import FunctionResult
from app.plugins.functions import FunctionRegistry
from app.plugins.events import EventBus, EventRegistry, HookDecision
from app.plugins.manager import PluginManager
from app.plugins.models import PluginManifest, PluginState
from app.plugins.package import build_package, verify_package


@dataclass(frozen=True, slots=True)
class DemoEvent(EventContract):
    value: str


class PluginTests(unittest.TestCase):
    def test_builtin_example_and_developer_readme_are_bootstrapped(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = PluginManager(root / "plugins", root / "registry.json")
            example = manager.get("lanctl.example.network-summary")
            self.assertEqual(example.state, PluginState.ENABLED)
            self.assertTrue((root / "plugins/readme.md").is_file())
            readme = (root / "plugins/readme.md").read_text(encoding="utf-8")
            self.assertIn("LANCTL.Network.Scan.Begin", readme)
            self.assertIn("inventory.summary", readme)
            manager.activate_enabled()
            commands = manager.extensions.list("command")
            self.assertEqual(commands[0].specification["name"], "network-summary")
            with self.assertRaises(PermissionError):
                manager.uninstall(example.manifest.plugin_id)

    def _source(self, root: Path, *, runtime="isolated", permissions=None) -> Path:
        source = root / "source"
        (source / "api").mkdir(parents=True)
        (source / "plugin.info").write_text(json.dumps({
            "schemaVersion": 1,
            "id": "demo.network-tools",
            "name": "Network Tools",
            "version": "1.0.0",
            "entryPoint": "main.exec",
            "runtime": runtime,
            "lanctl": {"minimumVersion": "0.3.0", "maximumVersion": "0.x"},
            "permissions": permissions or ["theme.register"],
            "capabilities": ["theme", "network"],
        }), encoding="utf-8")
        (source / "api/api.map").write_text(json.dumps({"extensions": [{
            "id": "demo.theme.dark", "type": "theme",
            "specification": {"palette": "dark"},
        }]}), encoding="utf-8")
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
            PluginManifest.from_dict({
                "schemaVersion": 2,
                "id": "demo.valid",
                "capabilities": ["plugin"],
            })

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
            self.assertEqual(manager.get(plugin.manifest.plugin_id).state, PluginState.ENABLED)
            self.assertEqual(manager.extensions.list("theme")[0].extension_id, "demo.theme.dark")
            manager.disable(plugin.manifest.plugin_id)
            self.assertEqual(manager.extensions.list(), [])

    def test_trusted_runtime_requires_explicit_trust(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / "trusted.lcp"
            build_package(self._source(root, runtime="trusted"), package)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            with self.assertRaises(PermissionError):
                manager.enable("demo.network-tools", grant={"theme.register"})
            plugin = manager.enable("demo.network-tools", grant={"theme.register"}, trusted=True)
            self.assertIsNotNone(plugin.module)

    def test_trusted_declared_hook_is_connected_to_event_bus(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = self._source(root, runtime="trusted", permissions=["theme.register", "events.listen"])
            hooks = source / "api/hooks"
            hooks.mkdir()
            (hooks / "startup.hook").write_text(json.dumps({
                "event": "LANCTL.Core.Lifecycle.Startup", "handler": "on_startup"
            }), encoding="utf-8")
            (source / "main.exec").write_text(
                "CALLED = []\n"
                "def on_startup(event):\n    CALLED.append(event.mode)\n"
                "def activate(api):\n    pass\n",
                encoding="utf-8",
            )
            package = root / "hooks.lcp"
            build_package(source, package)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            plugin = manager.enable("demo.network-tools", grant={"theme.register", "events.listen"}, trusted=True)
            manager.events.emit("LANCTL.Core.Lifecycle.Startup", {"version": "test", "mode": "unit"})
            self.assertEqual(plugin.module.CALLED, ["unit"])

    def test_event_bus_uses_contract_and_isolates_plugin_errors(self):
        audit = []
        registry = EventRegistry()
        registry.register("Demo.Network.Scan.Begin", DemoEvent, owner="demo")
        bus = EventBus(registry, lambda *parts: audit.append(parts))
        received = []
        bus.subscribe("Demo.Network.Scan.Begin", lambda event: received.append(event.value), plugin_id="demo.good")
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
            (source / "api/events.schema").write_text(json.dumps({"events": {
                "Demo.Network.Scan.Begin": {
                    "arguments": {"scan_id": "string", "target": "string?"}
                }
            }}), encoding="utf-8")
            package = root / "events.lcp"
            build_package(source, package)
            manager = PluginManager(root / "installed", root / "registry.json")
            manager.install(package)
            manager.enable("demo.network-tools", grant={"theme.register", "events.register"})
            event = manager.events.emit("Demo.Network.Scan.Begin", {"scan_id": "abc"}, source="demo.network-tools")
            self.assertEqual(event.scan_id, "abc")
            self.assertIsNone(event.target)
            self.assertIsInstance(event, EventContract)

    def test_function_registry_requires_the_declared_return_contract(self):
        registry = FunctionRegistry()
        registry.register("Demo.Core.Action.Run", lambda: FunctionResult(True), FunctionResult, owner="demo")
        self.assertTrue(registry.call("Demo.Core.Action.Run", caller="test").success)
        registry.register("Demo.Core.Action.Bad", lambda: {}, FunctionResult, owner="demo")
        with self.assertRaises(TypeError):
            registry.call("Demo.Core.Action.Bad", caller="test")


if __name__ == "__main__":
    unittest.main()
