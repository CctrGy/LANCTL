import json
import tempfile
import unittest
from pathlib import Path

from app.i18n import ENGLISH_STRINGS, LanguageManager


class LanguageTests(unittest.TestCase):
    def test_fresh_install_bootstraps_only_english(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = LanguageManager(temporary)
            manager.initialize("en")
            self.assertEqual([item.code for item in manager.list()], ["en"])
            self.assertTrue((Path(temporary) / "english.lang").is_file())
            self.assertTrue((Path(temporary) / "languajes.json").is_file())

    def test_missing_translation_falls_back_to_english(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = LanguageManager(root)
            manager.initialize("en")
            partial = root / "partial.lang"
            partial.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "meta": {"code": "xx", "name": "Test", "nativeName": "Test"},
                        "strings": {"LANCTL.COMMON.STATUS.ERROR": "ERR"},
                    }
                ),
                encoding="utf-8",
            )
            manager.discover()
            manager.select("xx")
            self.assertEqual(manager.translate("LANCTL.COMMON.STATUS.ERROR"), "ERR")
            self.assertEqual(
                manager.translate("LANCTL.CORE.APP.CANCELLED"),
                ENGLISH_STRINGS["LANCTL.CORE.APP.CANCELLED"],
            )

    def test_placeholder_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "broken.lang"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "meta": {"code": "xx", "name": "Test"},
                        "strings": {"LANCTL.LANGUAGE.ERROR.NOT_FOUND": "Missing"},
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                LanguageManager(temporary).load_file(path)

    def test_registry_keeps_selected_and_fallback_codes(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = LanguageManager(temporary)
            manager.initialize("en")
            registry = json.loads((Path(temporary) / "languajes.json").read_text(encoding="utf-8"))
            self.assertEqual(registry["selected"], "en")
            self.assertEqual(registry["fallback"], "en")


if __name__ == "__main__":
    unittest.main()
