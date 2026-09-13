import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.vlf import create_project
from lanctl.core.projects.workspace import (
    ProjectChangesPendingError,
    activate_project_workspace,
    ensure_active_project_workspace,
    prepare_project_workspace,
)


class ProjectWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.devices = self.root / "network-devices.json"
        self.groups = self.root / "network-groups.json"
        self.credentials = self.root / ".credentials"
        self.credentials.write_bytes(b"")
        self.groups.write_text("[]", encoding="utf-8")
        self.config = {
            "database": str(self.devices),
            "groups": str(self.groups),
            "credentials": str(self.credentials),
            "range": "192.168.1.0/24",
        }

    def tearDown(self):
        self.temporary.cleanup()

    def _create_project(self, filename: str, alias: str, mac_suffix: str) -> Path:
        self.devices.write_text(
            json.dumps(
                [
                    {
                        "IP": f"192.168.1.{int(mac_suffix, 16)}",
                        "MAC": f"AA:BB:CC:DD:EE:{mac_suffix}",
                        "cnf": "O",
                        "ALIAS": alias,
                        "NAME": alias,
                        "GROUP": [],
                        "description": "Inventario del proyecto",
                    }
                ]
            ),
            encoding="utf-8",
        )
        return Path(
            create_project(
                self.root / filename,
                name=alias,
                config=self.config,
            )["path"]
        )

    def test_switching_projects_switches_database_instead_of_network_scan(self):
        first = self._create_project("primero.vlf", "PROYECTO-UNO", "11")
        second = self._create_project("segundo.vlf", "PROYECTO-DOS", "22")
        settings = dict(self.config)

        def update(callback):
            replacement = callback(settings)
            if replacement is not None:
                settings.clear()
                settings.update(replacement)
            return dict(settings)

        with patch("lanctl.core.projects.workspace.update_config", side_effect=update):
            first_workspace = activate_project_workspace(
                first,
                config=settings,
                root=self.root / "workspaces",
            )
            first_aliases = [
                device.alias for device in DeviceDatabase(str(first_workspace.database)).load()
            ]
            second_workspace = activate_project_workspace(
                second,
                config=settings,
                root=self.root / "workspaces",
            )
            second_aliases = [
                device.alias for device in DeviceDatabase(str(second_workspace.database)).load()
            ]

        self.assertEqual(first_aliases, ["PROYECTO-UNO"])
        self.assertEqual(second_aliases, ["PROYECTO-DOS"])
        self.assertNotEqual(first_workspace.database, second_workspace.database)
        self.assertEqual(settings["database"], str(second_workspace.database))
        self.assertEqual(settings["networkDatabase"], str(self.devices))
        self.assertEqual(settings["networkGroups"], str(self.groups))

    @pytest.mark.legacy_gui
    def test_gui_returns_the_inventory_of_each_selected_project(self):
        from lanctl.apps.ip.interfaces.gui.main import GuiApi

        first = self._create_project("casa.vlf", "CASA", "31")
        second = self._create_project("taller.vlf", "TALLER", "32")
        settings = dict(self.config)

        def load():
            return dict(settings)

        def update(callback):
            replacement = callback(settings)
            if replacement is not None:
                settings.clear()
                settings.update(replacement)
            return dict(settings)

        with (
            patch("lanctl.apps.ip.interfaces.gui.main.load_config", side_effect=load),
            patch("lanctl.core.projects.workspace.load_config", side_effect=load),
            patch("lanctl.core.projects.workspace.update_config", side_effect=update),
            patch(
                "lanctl.core.projects.workspace.application_path",
                return_value=self.root / "gui-workspaces",
            ),
            patch(
                "lanctl.apps.ip.interfaces.gui.main.GuiApi._projects_payload",
                return_value={
                    "projects": [],
                    "activeProject": "",
                },
            ),
            patch("lanctl.apps.ip.interfaces.gui.main.get_plugin_manager"),
            patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"),
        ):
            api = GuiApi()
            first_result = api.use_project(str(first))
            second_result = api.use_project(str(second))

        self.assertTrue(first_result["ok"], first_result.get("error"))
        self.assertTrue(second_result["ok"], second_result.get("error"))
        self.assertEqual(first_result["devices"][0]["alias"], "CASA")
        self.assertEqual(second_result["devices"][0]["alias"], "TALLER")

    def test_startup_migrates_an_active_project_from_the_network_database(self):
        project = self._create_project("activo.vlf", "ACTIVO", "41")
        settings = {**self.config, "activeProject": str(project)}

        def load():
            return dict(settings)

        def update(callback):
            callback(settings)
            return dict(settings)

        with (
            patch("lanctl.core.projects.workspace.load_config", side_effect=load),
            patch("lanctl.core.projects.workspace.update_config", side_effect=update),
            patch(
                "lanctl.core.projects.workspace.application_path",
                return_value=self.root / "startup-workspaces",
            ),
        ):
            workspace = ensure_active_project_workspace()

        self.assertIsNotNone(workspace)
        self.assertEqual(settings["database"], str(workspace.database))
        self.assertEqual(
            DeviceDatabase(settings["database"]).load()[0].alias,
            "ACTIVO",
        )

    def test_missing_active_project_does_not_block_gui_startup(self):
        missing = self.root / "movido-o-borrado.vlf"
        with patch(
            "lanctl.core.projects.workspace.load_config",
            return_value={"activeProject": str(missing)},
        ):
            self.assertIsNone(ensure_active_project_workspace())

    def test_dirty_workspace_cannot_be_refreshed_without_explicit_discard(self):
        project = self._create_project("protegido.vlf", "ORIGINAL", "51")
        workspace = prepare_project_workspace(project, root=self.root / "protected")
        DeviceDatabase(str(workspace.database)).edit_device("ORIGINAL", "alias", "EDITADO")

        with self.assertRaises(ProjectChangesPendingError):
            prepare_project_workspace(project, root=self.root / "protected", refresh=True)

        preserved = DeviceDatabase(str(workspace.database)).load()[0]
        self.assertEqual(preserved.alias, "EDITADO")

    def test_switching_project_rejects_abandoning_dirty_active_workspace(self):
        first = self._create_project("primero.vlf", "UNO", "61")
        second = self._create_project("segundo.vlf", "DOS", "62")
        settings = dict(self.config)

        def update(callback):
            callback(settings)
            return dict(settings)

        with patch("lanctl.core.projects.workspace.update_config", side_effect=update):
            active = activate_project_workspace(
                first, config=settings, root=self.root / "switch-protected"
            )
            DeviceDatabase(str(active.database)).edit_device("UNO", "alias", "CAMBIO")
            with self.assertRaises(ProjectChangesPendingError):
                activate_project_workspace(
                    second, config=settings, root=self.root / "switch-protected"
                )

        self.assertEqual(Path(settings["activeProject"]), first.resolve())
        self.assertEqual(DeviceDatabase(str(active.database)).load()[0].alias, "CAMBIO")


if __name__ == "__main__":
    unittest.main()
