import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.database import DeviceDatabase
from app.gui import GuiApi
from app.gui_theme import (
    COMPONENT_IDS,
    DEFAULT_TOKENS,
    resolve_theme,
    validate_theme_specification,
)
from app.plugins.manager import PluginManager
from app.plugins.package import verify_package

ROOT = Path(__file__).resolve().parents[1]


class GuiIntegrationTests(unittest.TestCase):
    def test_active_project_outside_default_directory_is_included_in_selector(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            active = root / "externo" / "casa.vlf"
            with (
                patch(
                    "app.gui.load_config",
                    return_value={
                        "activeProject": str(active),
                        "projectsDirectory": str(root),
                    },
                ),
                patch(
                    "app.gui.active_project_info",
                    return_value={
                        "path": str(active),
                        "name": "Casa",
                        "id": "project-1",
                        "available": True,
                        "valid": True,
                    },
                ),
            ):
                payload = GuiApi()._projects_payload()
        self.assertEqual(payload["activeProject"], str(active))
        self.assertEqual(
            payload["projects"],
            [
                {
                    "path": str(active),
                    "name": "Casa",
                    "id": "project-1",
                }
            ],
        )

    def test_description_field_spans_the_full_editor_width(self):
        html = (ROOT / "gui/index.html").read_text(encoding="utf-8")
        css = (ROOT / "gui/styles.css").read_text(encoding="utf-8")
        self.assertRegex(
            html,
            r'<label class="description-field">Descripción<input id="edit-description"',
        )
        self.assertIn(
            ".editable-fields .description-field { grid-column:1/-1; }",
            css,
        )

    def test_main_layout_reserves_navigation_content_and_status_rows(self):
        html = (ROOT / "gui/index.html").read_text(encoding="utf-8")
        css = (ROOT / "gui/styles.css").read_text(encoding="utf-8")
        self.assertIn("grid-template-rows:54px 43px minmax(0,1fr) 28px", css)
        self.assertIn('id="activity-rows"', html)
        self.assertIn('id="project-open"', html)
        self.assertNotIn("background:#fff", css)

    def test_inventory_rows_expose_a_device_context_menu(self):
        html = (ROOT / "gui/index.html").read_text(encoding="utf-8")
        javascript = (ROOT / "gui/app.js").read_text(encoding="utf-8")
        css = (ROOT / "gui/styles.css").read_text(encoding="utf-8")
        self.assertIn('id="device-context-menu"', html)
        for action in (
            "select",
            "details",
            "reload",
            "diagnose",
            "open",
            "terminal",
            "wake",
            "delete",
        ):
            self.assertIn(f'data-context-action="{action}"', html)
        self.assertIn('addEventListener("contextmenu"', javascript)
        self.assertIn('call("delete_device",device.id,true)', javascript)
        self.assertIn(".context-menu", css)

    def test_local_gui_never_requests_remote_credentials(self):
        javascript = (ROOT / "gui/app.js").read_text(encoding="utf-8")
        self.assertIn(
            'window.location.protocol==="https:"||window.location.protocol==="http:"',
            javascript,
        )
        self.assertIn(
            'DOMContentLoaded",()=>{if(isRemoteClient())remoteLogin()}',
            javascript,
        )
        self.assertNotIn(
            'DOMContentLoaded",()=>{if(!window.pywebview?.api)remoteLogin()}',
            javascript,
        )

    def test_project_selection_replaces_the_visible_inventory(self):
        javascript = (ROOT / "gui/app.js").read_text(encoding="utf-8")
        self.assertRegex(
            javascript,
            r'call\("use_project"[^;]+;renderProjects\(payload\);'
            r"renderInventory\(payload\)",
        )

    def test_gui_api_creates_a_project_in_the_selected_directory(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("app.gui.create_project") as creator,
            patch("app.gui.activate_project_workspace"),
            patch(
                "app.gui.GuiApi._projects_payload",
                return_value={"projects": [], "activeProject": ""},
            ),
            patch(
                "app.gui.GuiApi._inventory_payload",
                return_value={"devices": [], "summary": {}},
            ),
        ):
            creator.return_value = {"path": str(Path(directory) / "Casa.vlf")}
            result = GuiApi().create_project("Casa", directory)
        self.assertTrue(result["ok"])
        self.assertEqual(creator.call_args.args[0], Path(directory) / "Casa")

    def test_html_component_ids_match_the_core_contract(self):
        html = (ROOT / "gui/index.html").read_text(encoding="utf-8")
        identifiers = set(re.findall(r'data-component-id="([^"]+)"', html))
        self.assertEqual(identifiers, set(COMPONENT_IDS))

    def test_bundled_theme_is_valid_and_activated_declaratively(self):
        package = ROOT / "bundled/lanctl.theme.default.lcp"
        result = verify_package(package)
        self.assertEqual(result["manifest"].plugin_id, "lanctl.theme.default")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = PluginManager(root / "plugins", root / "registry.json")
            manager.activate_enabled()
            themes = manager.extensions.list("theme")
            self.assertEqual(
                [theme.extension_id for theme in themes], ["lanctl.theme.default.palette"]
            )
            resolved = resolve_theme(themes)
            self.assertEqual(resolved["id"], "lanctl.theme.default.palette")
            self.assertEqual(len(resolved["tokens"]), len(DEFAULT_TOKENS))

    def test_theme_rejects_unknown_code_identifiers_and_css_injection(self):
        with self.assertRaisesRegex(ValueError, "identificadores GUI desconocidos"):
            validate_theme_specification({"components": {"lanctl.missing": {}}})
        with self.assertRaisesRegex(ValueError, "valor no válido"):
            validate_theme_specification({"tokens": {"color.accent": "red; display:none"}})

    def test_gui_reads_and_updates_inventory_using_stable_device_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = str(Path(temporary) / "devices.json")
            database = DeviceDatabase(database_path)
            device = database.add_device(
                "AA:BB:CC:DD:EE:FF",
                name="Switch",
                alias="SW-TEST",
                description="Inicial",
            )
            config = {
                "database": database_path,
                "timeout": 0.1,
                "workers": 1,
                "credentials": str(Path(temporary) / "credentials"),
            }
            with patch("app.gui.load_config", return_value=config):
                api = GuiApi()
                listed = api.list_devices()
                self.assertTrue(listed["ok"])
                self.assertEqual(listed["devices"][0]["id"], device.device_id)
                updated = api.update_device(
                    device.device_id,
                    {
                        "alias": "SW-GUI",
                        "name": "Core",
                        "description": "Desde GUI",
                    },
                )
                self.assertTrue(updated["ok"], updated.get("error"))
                saved = database.resolve(device.device_id)
                self.assertEqual(
                    (saved.alias, saved.name, saved.description), ("SW-GUI", "Core", "Desde GUI")
                )

    def test_gui_delete_requires_confirmation_and_removes_group_references(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database_path = str(root / "devices.json")
            groups_path = root / "groups.json"
            database = DeviceDatabase(database_path)
            device = database.add_device("AA:BB:CC:DD:EE:FE", name="Cámara", alias="CAM-GUI")
            groups_path.write_text(
                '[{"name":"IOT","description":"-","members":'
                '["AA:BB:CC:DD:EE:FE"],"editable":true}]',
                encoding="utf-8",
            )
            config = {
                "database": database_path,
                "groups": str(groups_path),
                "timeout": 0.1,
                "workers": 1,
                "credentials": str(root / "credentials"),
            }
            with patch("app.gui.load_config", return_value=config):
                api = GuiApi()
                rejected = api.delete_device(device.device_id, False)
                deleted = api.delete_device(device.device_id, True)

            self.assertFalse(rejected["ok"])
            self.assertTrue(deleted["ok"], deleted.get("error"))
            self.assertEqual(database.load(), [])
            self.assertNotIn("AA:BB:CC:DD:EE:FE", groups_path.read_text(encoding="utf-8"))

    def test_gui_exposes_local_host_as_ephemeral_at_cnf(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = str(Path(temporary) / "devices.json")
            database = DeviceDatabase(database_path)
            device = database.upsert(
                [{"IP": "192.168.50.10", "MAC": "AA:BB:CC:DD:EE:10", "cnf": "O"}]
            )[0]
            config = {
                "database": database_path,
                "timeout": 0.1,
                "workers": 1,
                "credentials": str(Path(temporary) / "credentials"),
            }
            with (
                patch("app.gui.load_config", return_value=config),
                patch("app.gui.local_ipv4", return_value="192.168.50.10"),
            ):
                api = GuiApi()
                listed = api.list_devices()
                self.assertEqual(listed["devices"][0]["cnf"], "@")
                self.assertEqual(database.resolve(device.device_id).cnf, "O")

    def test_gui_labels_services_and_exposes_only_interactive_actions(self):
        self.assertEqual(GuiApi._service_label("ssh"), "SSH · Terminal segura")
        self.assertEqual(GuiApi._service_label("ipp"), "IPP · Impresora")
        self.assertEqual(GuiApi._interactive_protocol("http-alt"), "http")
        self.assertIsNone(GuiApi._interactive_protocol("mysql"))

    def test_gui_opens_detected_http_service_on_its_real_port(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = str(Path(temporary) / "devices.json")
            database = DeviceDatabase(database_path)
            device = database.upsert([{"IP": "192.168.1.40", "MAC": "AA:BB:CC:DD:EE:40"}])[0]
            config = {
                "database": database_path,
                "timeout": 0.1,
                "workers": 1,
                "credentials": str(Path(temporary) / "credentials"),
            }
            with (
                patch("app.gui.load_config", return_value=config),
                patch("app.gui.run_open") as opened,
            ):
                result = GuiApi().open_service(device.device_id, "http-alt", 8080)
                self.assertTrue(result["ok"], result.get("error"))
                arguments = opened.call_args.args[0]
                self.assertEqual((arguments.protocol, arguments.port), ("http", 8080))

    def test_gui_opens_ssh_in_a_native_terminal_with_detected_port(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = str(Path(temporary) / "devices.json")
            database = DeviceDatabase(database_path)
            device = database.upsert([{"IP": "192.168.1.41", "MAC": "AA:BB:CC:DD:EE:41"}])[0]
            config = {
                "database": database_path,
                "timeout": 0.1,
                "workers": 1,
                "credentials": str(Path(temporary) / "credentials"),
            }
            with (
                patch("app.gui.load_config", return_value=config),
                patch("app.gui.subprocess.Popen") as opened,
            ):
                result = GuiApi().open_service(device.device_id, "ssh", 2222)
                self.assertTrue(result["ok"], result.get("error"))
                self.assertEqual(opened.call_args.args[0], ["ssh", "-p", "2222", "192.168.1.41"])

    def test_gui_exposes_wol_only_for_devices_with_a_mac(self):
        with tempfile.TemporaryDirectory() as temporary:
            database_path = str(Path(temporary) / "devices.json")
            database = DeviceDatabase(database_path)
            database.upsert(
                [{"IP": "192.168.1.50", "MAC": "02:11:22:33:44:55"}, {"IP": "192.168.1.51"}]
            )
            config = {
                "database": database_path,
                "timeout": 0.1,
                "workers": 1,
                "credentials": str(Path(temporary) / "credentials"),
            }
            with patch("app.gui.load_config", return_value=config):
                devices = GuiApi().list_devices()["devices"]
            self.assertEqual([item["wolAvailable"] for item in devices], [True, False])


if __name__ == "__main__":
    unittest.main()
