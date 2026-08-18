import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.projects.save_policy import (
    SaveMode,
    SaveTrigger,
    available_save_modes,
    close_active_project,
    normalize_save_mode,
    save_active_project,
    workspace_fingerprint,
    workspace_is_dirty,
)


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
        with patch("app.plugins.get_plugin_manager", return_value=manager):
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
                patch("app.projects.save_policy.load_config", return_value=settings),
                patch(
                    "app.projects.vlf.update_project",
                    return_value={"path": settings["activeProject"]},
                ) as update,
                patch(
                    "app.projects.workspace.activate_project_workspace",
                    return_value=workspace,
                ),
                patch("app.plugins.get_plugin_manager", return_value=manager),
                patch("app.projects.save_policy.write_log"),
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
                patch("app.projects.save_policy.load_config", return_value=settings),
                patch(
                    "app.projects.vlf.update_project",
                    return_value={"path": settings["activeProject"]},
                ) as update,
                patch(
                    "app.projects.workspace.activate_project_workspace",
                    return_value=workspace,
                ),
                patch("app.plugins.get_plugin_manager", return_value=manager),
                patch("app.projects.save_policy.write_log"),
            ):
                skipped = save_active_project(SaveTrigger.CLOSE)
                saved = save_active_project(force=True)

            self.assertFalse(skipped.saved)
            self.assertTrue(saved.saved)
            update.assert_called_once()

    def test_close_consult_saves_only_after_user_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = self._workspace(Path(directory), SaveMode.MANUAL_CLOSE_CONSULT.value)
            with (
                patch("app.projects.save_policy.load_config", return_value=settings),
                patch("app.projects.save_policy.save_active_project") as save,
            ):
                declined = close_active_project(input_fn=lambda _prompt: "n")
                accepted = close_active_project(input_fn=lambda _prompt: "s")

            self.assertEqual(declined.reason, "user-declined")
            self.assertFalse(declined.saved)
            save.assert_called_once_with(SaveTrigger.CLOSE, force=True, config=settings)
            self.assertIs(accepted, save.return_value)

    def test_timed_mode_uses_timer_trigger(self):
        definitions = {item.mode: item for item in available_save_modes()}
        self.assertEqual(
            definitions[SaveMode.TIME_TO_SAVE.value].triggers,
            frozenset({SaveTrigger.TIMER.value}),
        )


if __name__ == "__main__":
    unittest.main()
