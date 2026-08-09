import json
import multiprocessing
import tempfile
import unittest
from pathlib import Path

from app.core.file_transaction import InterProcessLock, atomic_write_json, update_json


def _increment_json(path: str, repetitions: int) -> None:
    for _ in range(repetitions):

        def increment(value):
            value["count"] += 1

        update_json(path, lambda: {"count": 0}, increment)


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


if __name__ == "__main__":
    unittest.main()
