import json
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


if __name__ == "__main__":
    unittest.main()
