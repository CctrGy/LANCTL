from __future__ import annotations

import os
import sys
from threading import Lock


class ScanProgress:
    """Progreso compacto; queda silencioso cuando stdout no es interactivo."""

    def __init__(self, enabled: bool = True, stream=None):
        self.stream = stream or sys.stdout
        self.enabled = enabled and self.stream.isatty() and "NO_PROGRESS" not in os.environ
        self.phase_name = ""
        self.total = 0
        self.current = 0
        self._lock = Lock()

    def start(self, phase: str, total: int) -> None:
        with self._lock:
            self.phase_name, self.total, self.current = phase, max(1, total), 0
            self._draw()

    def advance(self, amount: int = 1) -> None:
        with self._lock:
            self.current = min(self.total, self.current + amount)
            self._draw()

    def finish(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            self.current = self.total
            self._draw()
            self.stream.write("\n")
            self.stream.flush()

    def _draw(self) -> None:
        if not self.enabled:
            return
        ratio = self.current / self.total
        width = 24
        filled = round(width * ratio)
        bar = "█" * filled + "─" * (width - filled)
        self.stream.write(
            f"\r{self.phase_name:<12} [{bar}] {ratio:>6.1%} {self.current}/{self.total}"
        )
        self.stream.flush()
