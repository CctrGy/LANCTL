import unittest
from pathlib import Path

from app.protocols.radmin import build_arguments, validate_mode


class RadminProtocolTests(unittest.TestCase):
    def test_documented_modes_and_quality_options(self):
        arguments = build_arguments(
            Path("Radmin.exe"),
            "192.168.1.20",
            4899,
            "view",
            through="192.168.1.2:4900",
            fullscreen=True,
            color_depth=16,
            updates=30,
        )
        self.assertEqual(arguments[1], "/connect:192.168.1.20:4899")
        for expected in (
            "/noinput",
            "/through:192.168.1.2:4900",
            "/fullscreen",
            "/16bpp",
            "/updates:30",
        ):
            self.assertIn(expected, arguments)

    def test_operational_modes_are_explicit(self):
        for mode, switch in (
            ("file", "/file"),
            ("shutdown", "/shutdown"),
            ("chat", "/chat"),
            ("voice", "/voice"),
            ("message", "/message"),
            ("telnet", "/telnet"),
        ):
            self.assertEqual(
                build_arguments("Radmin.exe", "host", mode=mode)[-1],
                switch,
            )
        with self.assertRaises(ValueError):
            validate_mode("password")

    def test_rejects_incompatible_or_unbounded_options(self):
        with self.assertRaises(ValueError):
            build_arguments("Radmin.exe", "host", mode="chat", fullscreen=True)
        with self.assertRaises(ValueError):
            build_arguments("Radmin.exe", "host", updates=1000)
        with self.assertRaises(ValueError):
            build_arguments("Radmin.exe", "host", through="gateway")


if __name__ == "__main__":
    unittest.main()
