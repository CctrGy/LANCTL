"""One GUI per launcher and local principal, protected for the process lifetime."""

from __future__ import annotations

import hashlib
import os
import re
import threading
import time

from lanctl.core.coordination import Coordinator
from lanctl.core.file_transaction import InterProcessLock

_active = set()
_guard = threading.Lock()


def allow_foreground(pid):
    if os.name == "nt":
        import ctypes

        ctypes.windll.user32.AllowSetForegroundWindow(int(pid))


def focus_gui(coordinator, launcher, *, timeout=30):
    """Wait for a ready GUI and an acknowledged focus request, never spawn one."""
    deadline = time.monotonic() + timeout
    command = None
    while time.monotonic() < deadline:
        if command is None:
            for session in reversed(coordinator.sessions()):
                if (
                    session["launcher"] == launcher
                    and session["mode"] == "gui"
                    and session["controls"]
                ):
                    allow_foreground(session["pid"])
                    command = coordinator.enqueue(session["id"], "view", "gui")
                    break
        else:
            with coordinator.connection() as db:
                row = db.execute(
                    "SELECT state FROM commands WHERE id=? AND owner=?",
                    (command, coordinator.owner),
                ).fetchone()
            if row and row[0] == "accepted":
                return
            if row and row[0] in {"failed", "expired"}:
                raise RuntimeError(f"La GUI de {launcher.upper()} no pudo ponerse al frente")
        time.sleep(0.05)
    raise TimeoutError(f"La GUI de {launcher.upper()} no responde; no se abrirá otra ventana")


class GuiInstance:
    def __init__(self, launcher, *, coordinator=None, timeout=30):
        if not re.fullmatch(r"lan[a-z]+", launcher):
            raise ValueError("launcher GUI no válido")
        self.launcher = launcher
        self.coordinator = coordinator or Coordinator()
        identity = hashlib.sha256(self.coordinator.owner.encode()).hexdigest()[:24]
        path = self.coordinator.path.parent / f"gui-{identity}-{launcher}.lock"
        self.lock = InterProcessLock(path, timeout=0)
        self.key = str(path.resolve())
        self.timeout = timeout
        self.owned = False

    def __enter__(self):
        with _guard:
            available = self.key not in _active
            if available:
                _active.add(self.key)
        if available:
            try:
                self.lock.acquire()
                self.owned = True
                return True
            except TimeoutError:
                with _guard:
                    _active.discard(self.key)
            except Exception:
                with _guard:
                    _active.discard(self.key)
                raise
        focus_gui(self.coordinator, self.launcher, timeout=self.timeout)
        return False

    def __exit__(self, *_args):
        if self.owned:
            try:
                self.lock.release()
            finally:
                self.owned = False
                with _guard:
                    _active.discard(self.key)
