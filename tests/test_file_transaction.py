import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from lanctl.core.file_transaction import (
    InterProcessLock,
    atomic_write_bytes,
    atomic_write_json,
    load_json_unlocked,
    update_json,
)


def _increment_json(path: str, repetitions: int) -> None:
    for _ in range(repetitions):

        def increment(value):
            value["count"] += 1

        update_json(path, lambda: {"count": 0}, increment)


def _hold_lock(path: str, ready, release) -> None:
    with InterProcessLock(path):
        ready.set()
        release.wait(10)


class FileTransactionTests(unittest.TestCase):
    def test_same_lock_instance_remains_owned_until_final_release(self):
        with tempfile.TemporaryDirectory() as temporary:
            lock = InterProcessLock(Path(temporary) / "state.lock")
            lock.acquire()
            lock.acquire()
            lock.acquire()
            lock.release()
            lock.release()
            self.assertIsNotNone(lock._stream)
            lock.release()
            self.assertIsNone(lock._stream)

    def test_atomic_json_uses_utf8_and_trailing_newline(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            atomic_write_json(path, {"nombre": "España"})
            self.assertEqual(path.read_text(encoding="utf-8"), '{\n  "nombre": "España"\n}\n')

    def test_parallel_processes_do_not_lose_json_updates(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            context = multiprocessing.get_context("spawn")
            processes = [
                context.Process(target=_increment_json, args=(str(path), 12)) for _ in range(3)
            ]
            for process in processes:
                process.start()
            for process in processes:
                process.join(15)
                self.assertEqual(process.exitcode, 0)

            self.assertEqual(
                json.loads(path.read_text(encoding="utf-8")),
                {"count": 36},
            )

    def test_lock_timeout_between_processes_is_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "state.lock")
            context = multiprocessing.get_context("spawn")
            ready, release = context.Event(), context.Event()
            process = context.Process(target=_hold_lock, args=(path, ready, release))
            process.start()
            try:
                self.assertTrue(ready.wait(10))
                with self.assertRaises(TimeoutError):
                    InterProcessLock(path, timeout=0.1).acquire()
            finally:
                release.set()
                process.join(10)
            self.assertEqual(process.exitcode, 0)

    def test_interrupted_atomic_replace_preserves_original_and_cleans_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.bin"
            path.write_bytes(b"original")
            with (
                patch(
                    "lanctl.core.file_transaction.os.replace",
                    side_effect=OSError("simulated interruption"),
                ),
                self.assertRaises(OSError),
            ):
                atomic_write_bytes(path, b"replacement")
            self.assertEqual(path.read_bytes(), b"original")
            self.assertEqual(list(path.parent.glob(f".{path.name}.*.tmp")), [])

    def test_invalid_update_does_not_replace_existing_json(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            atomic_write_json(path, {"count": 1})

            def reject(_value):
                raise ValueError("invalid state")

            with self.assertRaises(ValueError):
                update_json(path, dict, lambda value: value.update(count=2), validate=reject)
            self.assertEqual(load_json_unlocked(path, dict), {"count": 1})

    def test_corrupt_json_is_never_silently_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "state.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                update_json(path, dict, lambda value: value)
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
