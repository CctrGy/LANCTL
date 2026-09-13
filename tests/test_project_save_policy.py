import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lanctl.core.database import DeviceDatabase
from lanctl.core.projects.save_policy import (
    SaveMode,
    SaveTrigger,
    available_save_modes,
    close_active_project,
    normalize_save_mode,
    save_active_project,
    workspace_fingerprint,
    workspace_is_dirty,
)
from lanctl.core.projects.vlf import create_project
from lanctl.core.projects.workspace import prepare_project_workspace


class ProjectSavePolicyTests(unittest.TestCase):
    def _workspace(self, root: Path, mode: str, *, dirty: bool = True) -> dict:
        database = root / "devices.json"
        groups = root / "groups.json"
        metadata = root / "workspace.json"
        database.write_text('[{"ip":"192.168.1.1"}]', encoding="utf-8")
        groups.write_text("[]", encoding="utf-8")
        settings = {
            "activeProject": str(root / "Casa.vlf"),
            "projectSaveMode": mode,
            "database": str(database),
            "groups": str(groups),
            "projectWorkspace": {
                "database": str(database),
                "groups": str(groups),
                "metadata": str(metadata),
            },
        }
        current = workspace_fingerprint(settings)
        metadata.write_text(
            json.dumps({"workspaceHash": "outdated" if dirty else current}), encoding="utf-8"
        )
        return settings

    def test_builtin_modes_and_legacy_double_dot_are_normalized(self):
        self.assertEqual(normalize_save_mode("manual"), SaveMode.MANUAL.value)
        self.assertEqual(normalize_save_mode("automatic..allChanges"), SaveMode.ALL_CHANGES.value)
        self.assertEqual(normalize_save_mode("AUTOMATIC.TOSCAN"), SaveMode.TO_SCAN.value)
        self.assertEqual(normalize_save_mode("automatic.timeToSAve"), SaveMode.TIME_TO_SAVE.value)

    def test_workspace_fingerprint_detects_real_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = self._workspace(Path(directory), SaveMode.ALL_CHANGES.value, dirty=False)
            self.assertFalse(workspace_is_dirty(settings))
            Path(settings["database"]).write_text("[]", encoding="utf-8")
            self.assertTrue(workspace_is_dirty(settings))

    def test_plugin_can_register_an_additional_save_mode(self):
        extension = SimpleNamespace(
            extension_id="nightly",
            owner="ExamplePlugin",
            specification={
                "mode": "plugin.nightly",
                "triggers": ["close"],
                "description": "Guarda al terminar la sesión.",
            },
        )
        manager = SimpleNamespace(
            extensions=SimpleNamespace(
                list=lambda kind: [extension] if kind == "project-save-mode" else []
            )
        )
        with patch("lanctl.core.plugins.get_plugin_manager", return_value=manager):
            modes = available_save_modes()
            self.assertEqual(normalize_save_mode("PLUGIN.NIGHTLY"), "plugin.nightly")

        plugin_mode = next(item for item in modes if item.mode == "plugin.nightly")
        self.assertEqual(plugin_mode.triggers, frozenset({"close"}))
        self.assertEqual(plugin_mode.owner, "ExamplePlugin")

    def test_scan_mode_saves_only_for_scan_and_only_when_dirty(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = self._workspace(Path(directory), SaveMode.TO_SCAN.value)
            workspace = SimpleNamespace(project_id="project-1")
            manager = SimpleNamespace(events=SimpleNamespace(emit=lambda *_args, **_kwargs: None))
            with (
                patch("lanctl.core.projects.save_policy.load_config", return_value=settings),
                patch(
                    "lanctl.core.projects.vlf.update_project",
                    return_value={"path": settings["activeProject"]},
                ) as update,
                patch(
                    "lanctl.core.projects.save_policy._verify_saved_workspace",
                    return_value={"verified": {}, "project": {"id": workspace.project_id}},
                ),
                patch("lanctl.core.plugins.get_plugin_manager", return_value=manager),
                patch("lanctl.core.projects.save_policy.write_log"),
            ):
                skipped = save_active_project(SaveTrigger.CHANGE)
                saved = save_active_project(SaveTrigger.SCAN)

            self.assertFalse(skipped.saved)
            self.assertTrue(saved.saved)
            update.assert_called_once()

    def test_manual_force_is_the_explicit_save_operation(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = self._workspace(Path(directory), SaveMode.MANUAL.value)
            workspace = SimpleNamespace(project_id="project-1")
            manager = SimpleNamespace(events=SimpleNamespace(emit=lambda *_args, **_kwargs: None))
            with (
                patch("lanctl.core.projects.save_policy.load_config", return_value=settings),
                patch(
                    "lanctl.core.projects.vlf.update_project",
                    return_value={"path": settings["activeProject"]},
                ) as update,
                patch(
                    "lanctl.core.projects.save_policy._verify_saved_workspace",
                    return_value={"verified": {}, "project": {"id": workspace.project_id}},
                ),
                patch("lanctl.core.plugins.get_plugin_manager", return_value=manager),
                patch("lanctl.core.projects.save_policy.write_log"),
            ):
                skipped = save_active_project(SaveTrigger.CLOSE)
                saved = save_active_project(force=True)

            self.assertFalse(skipped.saved)
            self.assertTrue(saved.saved)
            update.assert_called_once()

    def test_manual_save_persists_workspace_inventory_inside_real_vlf(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "Casa.vlf"
            database_path = root / "devices.json"
            groups_path = root / "groups.json"
            database = DeviceDatabase(str(database_path))
            database.add_device("02:00:00:00:00:21", alias="NAS")
            settings = {
                "database": str(database_path),
                "groups": str(groups_path),
                "activeProject": str(project),
                "projectSaveMode": SaveMode.MANUAL.value,
                "range": "192.168.1.0/24",
            }
            create_project(project, name="Casa", config=settings)
            metadata = root / "workspace.json"
            settings["projectWorkspace"] = {
                "database": str(database_path),
                "groups": str(groups_path),
                "metadata": str(metadata),
            }
            metadata.write_text(
                json.dumps({"workspaceHash": workspace_fingerprint(settings)}),
                encoding="utf-8",
            )
            database.edit_device("NAS", "description", "Cambio pendiente")
            manager = SimpleNamespace(
                events=SimpleNamespace(emit=lambda *_args, **_kwargs: None),
                project_registry=lambda: {"schemaVersion": 1, "plugins": []},
            )

            with (
                patch("lanctl.core.plugins.get_plugin_manager", return_value=manager),
                patch("lanctl.core.projects.save_policy.write_log"),
            ):
                result = save_active_project(force=True, config=settings)

            extracted = prepare_project_workspace(project, root=root / "extracted")
            stored = DeviceDatabase(str(extracted.database)).resolve("NAS")
            self.assertTrue(result.saved)
            self.assertEqual(stored.description, "Cambio pendiente")
            self.assertFalse(workspace_is_dirty(settings))
            self.assertTrue(Path(str(project) + ".bak").is_file())
            recovery = list((root / ".lanctl-backups").glob("Casa-*.vlf"))
            self.assertEqual(len(recovery), 1)

    def test_close_consult_saves_only_after_user_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = self._workspace(Path(directory), SaveMode.MANUAL_CLOSE_CONSULT.value)
            with (
                patch("lanctl.core.projects.save_policy.load_config", return_value=settings),
                patch("lanctl.core.projects.save_policy.save_active_project") as save,
            ):
                declined = close_active_project(input_fn=lambda _prompt: "n")
                accepted = close_active_project(input_fn=lambda _prompt: "s")

            self.assertEqual(declined.reason, "user-declined")
            self.assertFalse(declined.saved)
            save.assert_called_once_with(SaveTrigger.CLOSE, force=True, config=settings)
            self.assertIs(accepted, save.return_value)

    def test_user_facing_consult_to_close_alias_is_supported(self):
        self.assertEqual(
            normalize_save_mode("manual.consultToClose"),
            SaveMode.MANUAL_CLOSE_CONSULT.value,
        )

    def test_timed_mode_uses_timer_trigger(self):
        definitions = {item.mode: item for item in available_save_modes()}
        self.assertEqual(
            definitions[SaveMode.TIME_TO_SAVE.value].triggers,
            frozenset({SaveTrigger.TIMER.value}),
        )


if __name__ == "__main__":
    unittest.main()
