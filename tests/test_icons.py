import json
import tempfile
import unittest
from pathlib import Path

from app.assets.icons import IconManager, jpeg_dimensions


def fake_jpeg(width: int, height: int) -> bytes:
    # Contenedor estructural mínimo suficiente para probar el lector SOF.
    return (
        b"\xff\xd8\xff\xc0\x00\x0b\x08"
        + height.to_bytes(2, "big") + width.to_bytes(2, "big")
        + b"\x01\x01\x11\x00\xff\xd9"
    )


class IconTests(unittest.TestCase):
    def test_empty_manager_creates_registry_without_terminal_integration(self):
        with tempfile.TemporaryDirectory() as temporary:
            manager = IconManager(temporary)
            manager.initialize()
            registry = json.loads((Path(temporary) / "icons.json").read_text(encoding="utf-8"))
            self.assertEqual(registry["format"], {"mime": "image/jpeg", "width": 125, "height": 125})
            self.assertEqual(registry["icons"], [])

    def test_registers_and_resolves_125_square_jpeg(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.jpg"
            source.write_bytes(fake_jpeg(125, 125))
            manager = IconManager(root / "icons")
            entry = manager.register(source, icon_id="device.router", name="Router")
            self.assertEqual((entry.width, entry.height), (125, 125))
            self.assertEqual(manager.resolve("device.router"), root / "icons/device.router.jpg")
            self.assertEqual(manager.list()[0].name, "Router")

    def test_rejects_wrong_dimensions_and_non_jpeg(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wrong = root / "wrong.jpg"
            wrong.write_bytes(fake_jpeg(64, 64))
            manager = IconManager(root / "icons")
            with self.assertRaises(ValueError):
                manager.register(wrong)
            text = root / "fake.jpg"
            text.write_text("not an image", encoding="utf-8")
            with self.assertRaises(ValueError):
                jpeg_dimensions(text)

    def test_invalid_file_does_not_prevent_catalog_startup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "broken.jpg").write_text("broken", encoding="utf-8")
            manager = IconManager(root)
            manager.initialize()
            self.assertEqual(manager.list(), [])
            self.assertEqual(manager.errors[0]["file"], "broken.jpg")


if __name__ == "__main__":
    unittest.main()
