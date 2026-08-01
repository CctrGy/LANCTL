import re
import tempfile
import unittest
from pathlib import Path

from app.gui_theme import COMPONENT_IDS, DEFAULT_TOKENS, resolve_theme, validate_theme_specification
from app.plugins.manager import PluginManager
from app.plugins.package import verify_package


ROOT = Path(__file__).resolve().parents[1]


class GuiIntegrationTests(unittest.TestCase):
    def test_html_component_ids_match_the_core_contract(self):
        html = (ROOT / "GUI/index.html").read_text(encoding="utf-8")
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
            self.assertEqual([theme.extension_id for theme in themes], ["lanctl.theme.default.palette"])
            resolved = resolve_theme(themes)
            self.assertEqual(resolved["id"], "lanctl.theme.default.palette")
            self.assertEqual(len(resolved["tokens"]), len(DEFAULT_TOKENS))

    def test_theme_rejects_unknown_code_identifiers_and_css_injection(self):
        with self.assertRaisesRegex(ValueError, "identificadores GUI desconocidos"):
            validate_theme_specification({"components": {"lanctl.missing": {}}})
        with self.assertRaisesRegex(ValueError, "valor no válido"):
            validate_theme_specification({"tokens": {"color.accent": "red; display:none"}})


if __name__ == "__main__":
    unittest.main()
