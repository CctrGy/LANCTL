"""Read-only, incremental follower of the shared operational log."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

from lanctl.apps.monitor.event_view import _date, _rows
from lanctl.core.config import load_config
from lanctl.core.paths import application_path


class LogFollower:
    def __init__(self, directory, limit=100):
        self.directory = Path(directory)
        self.limit = limit
        self.positions = {}
        self.pending = {}
        self.initialized = False

    def poll(self):
        rows = []
        paths = sorted(self.directory.glob("*.log"), key=lambda path: (_date(path.name), path.name))
        if not self.initialized:
            paths = paths[-5:]
        for path in paths:
            try:
                stream = path.open("rb")
            except FileNotFoundError:
                continue  # normal rotation/retention race
            with stream:
                stat = os.fstat(stream.fileno())
                identity = (stat.st_dev, stat.st_ino)
                previous = self.positions.get(path)
                start = previous[1] if previous and previous[0] == identity else 0
                if start > stat.st_size:
                    start = 0
                    self.pending.pop(path, None)
                if previous and previous[0] != identity:
                    self.pending.pop(path, None)
                if not self.initialized:
                    start = max(0, stat.st_size - 1024 * 1024)
                    stream.seek(start)
                    if start:
                        stream.readline()  # skip a partial first line
                else:
                    stream.seek(start)
                chunk = stream.read(1024 * 1024)
                self.positions[path] = (identity, stream.tell())
            data = self.pending.pop(path, b"") + chunk
            lines = data.split(b"\n")
            self.pending[path] = lines.pop()[-65536:]
            for line in lines:
                rows.extend(_rows(line.decode("utf-8", errors="replace"), "program", path.name, 1))
        if not self.initialized:
            # Record older files at EOF, without displaying their history later.
            for path in self.directory.glob("*.log"):
                if path not in self.positions:
                    try:
                        stat = path.stat()
                    except FileNotFoundError:
                        continue
                    self.positions[path] = ((stat.st_dev, stat.st_ino), stat.st_size)
            rows = list(deque(rows, maxlen=self.limit))
        live = set(self.directory.glob("*.log"))
        self.positions = {path: value for path, value in self.positions.items() if path in live}
        self.pending = {path: value for path, value in self.pending.items() if path in live}
        self.initialized = True
        return rows


def follow_logs(*, limit=100, minimum=1):
    if not 1 <= limit <= 1000 or not 1 <= minimum <= 59:
        raise ValueError("limit debe estar entre 1-1000 y level entre 1-59")
    directory = application_path(load_config()["programLog"])
    follower = LogFollower(directory, limit)
    print(f"LANCTL · Log unificado · {directory}\nCtrl+C para cerrar el seguimiento.", flush=True)
    try:
        while True:
            for row in follower.poll():
                if row["level"] is None or row["level"] >= minimum:
                    print(f"[{row['file']}] {row['message']}", flush=True)
            time.sleep(0.3)
    except KeyboardInterrupt:
        return 0


def open_log_window(*, limit=100, minimum=1):
    if not 1 <= limit <= 1000 or not 1 <= minimum <= 59:
        raise ValueError("limit debe estar entre 1-1000 y level entre 1-59")
    if getattr(sys, "frozen", False):
        command = [
            str(Path(sys.executable).with_name("lanmon.exe" if os.name == "nt" else "lanmon"))
        ]
    else:
        command = [sys.executable, str(Path(__file__).resolve().parents[4] / "lanmon.py")]
    command += [
        "logs",
        "--follow",
        "--source",
        "program",
        "--limit",
        str(limit),
        "--level",
        str(minimum),
    ]
    if os.name == "nt":
        subprocess.Popen(command, creationflags=subprocess.CREATE_NEW_CONSOLE)
    else:
        terminal = shutil.which("x-terminal-emulator") or shutil.which("xterm")
        if not terminal:
            raise RuntimeError("No hay terminal gráfica disponible; usa lanmon logs --follow.")
        subprocess.Popen([terminal, "-e", *command])
    return 0
