import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from app.access import root_control


class RootControlTests(unittest.TestCase):
    def test_interface_status_requires_matching_identity_and_fresh_heartbeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime.json"
            runtime.write_text(
                json.dumps(
                    {
                        "pid": 123,
                        "identity": "process-identity",
                        "heartbeat": time.time(),
                        "mode": "tui",
                        "interactive": True,
                    }
                ),
                encoding="utf-8",
            )
            with patch.object(root_control, "_identity", return_value="process-identity"):
                self.assertTrue(root_control.interface_status(runtime)["running"])
            with patch.object(root_control, "_identity", return_value="another-process"):
                self.assertFalse(root_control.interface_status(runtime)["running"])

    def test_enqueue_targets_the_active_root_interface(self):
        with tempfile.TemporaryDirectory() as temporary:
            command_path = Path(temporary) / "commands.json"
            status = {"running": True, "mode": "gui", "pid": 456, "interactive": True}
            with (
                patch.object(root_control, "COMMAND_PATH", command_path),
                patch.object(root_control, "interface_status", return_value=status),
            ):
                result = root_control.enqueue("refresh")

            queued = json.loads(command_path.read_text(encoding="utf-8"))
            self.assertTrue(result["queued"])
            self.assertEqual(queued[0]["action"], "refresh")
            self.assertEqual(queued[0]["targetPid"], 456)

    def test_interface_agent_consumes_only_commands_for_its_process(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            handled = []
            agent = root_control.RootInterfaceAgent(
                "tui", handled.append, root / "runtime.json", root / "commands.json"
            )
            (root / "commands.json").write_text(
                json.dumps(
                    [
                        {"targetPid": agent.pid, "action": "refresh"},
                        {"targetPid": agent.pid + 1, "action": "view"},
                    ]
                ),
                encoding="utf-8",
            )

            commands = agent._commands()

            self.assertEqual([item["action"] for item in commands], ["refresh"])
            remaining = json.loads((root / "commands.json").read_text(encoding="utf-8"))
            self.assertEqual([item["action"] for item in remaining], ["view"])

    def test_root_status_combines_backend_and_interface_state(self):
        access_status = {
            "ssh": {"enabled": True, "bind": "127.0.0.1", "port": 2222, "running": False},
            "https": {"enabled": False, "running": False},
        }

        class FakeAccessService:
            def __init__(self, *_arguments):
                pass

            def status(self):
                return access_status

        connection = unittest.mock.MagicMock()
        connection.__enter__.return_value = connection
        with (
            patch("app.access.service.AccessService", FakeAccessService),
            patch(
                "app.core.config.load_config",
                return_value={"accessConfig": "a", "accessUsers": "u"},
            ),
            patch.object(root_control, "application_path", side_effect=Path),
            patch.object(
                root_control,
                "interface_status",
                return_value={"running": True, "mode": "tui", "pid": 1, "interactive": True},
            ),
            patch.object(root_control.socket, "create_connection", return_value=connection),
        ):
            status = root_control.root_status()

        self.assertEqual(status["state"], "TUI+BACKEND")
        self.assertTrue(status["backend"]["ssh"]["listening"])

    def test_forced_view_queues_inside_an_active_tui(self):
        current = {"running": True, "mode": "tui", "pid": 44, "interactive": True}
        with (
            patch.object(root_control, "interface_status", return_value=current),
            patch.object(root_control, "enqueue", return_value={"queued": True}) as enqueue,
        ):
            result = root_control.forced_view("settings")

        self.assertTrue(result["queued"])
        enqueue.assert_called_once_with("view", "settings")

    def test_forced_view_launches_a_new_process_when_no_interface_exists(self):
        current = {"running": False, "mode": None, "pid": None, "interactive": False}
        process = unittest.mock.MagicMock(pid=789)
        with (
            patch.object(root_control, "interface_status", return_value=current),
            patch.object(root_control, "_command", return_value=["lanctl", "--tui", "plugins"]),
            patch.object(root_control.subprocess, "Popen", return_value=process) as popen,
            patch.object(root_control.platform, "system", return_value="Windows"),
            patch.object(root_control.os, "name", "nt"),
        ):
            result = root_control.forced_view("plugins")

        self.assertEqual(result["pid"], 789)
        self.assertIn("Session 0", result["warning"])
        popen.assert_called_once()

    def test_interface_agent_publishes_heartbeat_and_cleans_it_on_stop(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runtime = root / "runtime.json"
            commands = root / "commands.json"
            with patch.object(root_control, "_identity", return_value="identity"):
                agent = root_control.RootInterfaceAgent(
                    "gui", lambda _command: None, runtime, commands
                )
                agent.start()
                published = json.loads(runtime.read_text(encoding="utf-8"))
                self.assertEqual(published["mode"], "gui")
                self.assertEqual(published["pid"], os.getpid())
                agent.stop()
            self.assertFalse(runtime.exists())


if __name__ == "__main__":
    unittest.main()
