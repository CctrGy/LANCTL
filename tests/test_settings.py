import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from lanctl.apps.ip.interfaces.cli.main import build_parser
from lanctl.core.config import DEFAULTS


class SettingsTests(unittest.TestCase):
    def test_physical_database_is_exposed_without_opening_it_as_json(self):
        args = build_parser().parse_args(
            ["settings", "--physical-database", "data/lc/physical/custom.db"]
        )
        with (
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.settings.load_config",
                return_value=deepcopy(DEFAULTS),
            ),
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.settings.save_config",
                return_value=Path("config.json"),
            ) as save,
            patch("lanctl.apps.ip.interfaces.cli.commands.settings.ok"),
        ):
            self.assertEqual(args.handler(args), 0)
        self.assertEqual(save.call_args.args[0]["physicalDatabase"], "data/lc/physical/custom.db")

    def test_remote_values_are_saved_when_service_application_needs_elevation(self):
        args = build_parser().parse_args(
            [
                "settings",
                "--remote-bind",
                "192.168.1.31",
                "--remote-cidr",
                "192.168.1.0/24",
                "--remote-port",
                "22",
            ]
        )
        with (
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.settings.load_config",
                return_value=deepcopy(DEFAULTS),
            ),
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.settings.save_config",
                return_value=Path("C:/ProgramData/LANCTL/config/config.json"),
            ) as save,
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.settings._configure_remote_access",
                side_effect=PermissionError("elevación requerida"),
            ),
            patch("lanctl.apps.ip.interfaces.cli.commands.settings.ok") as report,
        ):
            result = args.handler(args)

        self.assertEqual(result, 0)
        saved = save.call_args.args[0]
        self.assertEqual(saved["remoteAccessBind"], "192.168.1.31")
        self.assertEqual(saved["remoteAccessPort"], 22)
        self.assertIn("valores guardados", report.call_args.args[1])

    def test_tui_keys_and_footer_buttons_are_validated_and_saved(self):
        args = build_parser().parse_args(
            [
                "settings",
                "--tui-key",
                "save=F4",
                "--tui-key",
                "copyLine=CTRL+S",
                "--tui-key",
                "deviceHistory=F6",
                "--tui-footer-buttons",
                "help,save,copyLine,exit",
                "--tui-footer-button",
                "help=off",
            ]
        )
        with (
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.settings.load_config",
                return_value=deepcopy(DEFAULTS),
            ),
            patch(
                "lanctl.apps.ip.interfaces.cli.commands.settings.save_config",
                return_value=Path("config.json"),
            ) as save,
            patch("lanctl.apps.ip.interfaces.cli.commands.settings.ok"),
        ):
            self.assertEqual(args.handler(args), 0)

        saved = save.call_args.args[0]
        self.assertEqual(saved["tuiKeyBindings"]["save"], "F4")
        self.assertEqual(saved["tuiKeyBindings"]["copyLine"], "CTRL_S")
        self.assertEqual(saved["tuiKeyBindings"]["deviceHistory"], "F6")
        self.assertIsNone(saved["tuiKeyBindings"]["projectStatus"])
        self.assertEqual(saved["tuiFooterButtons"], ["save", "copyLine", "exit"])


if __name__ == "__main__":
    unittest.main()
