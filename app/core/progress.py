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
        self.found_total = 0
        self._found_keys: set[str] = set()
        self._known_identities: dict[str, str] = {}
        self._visible_width = 0
        self._lock = Lock()

    def begin(
        self,
        total: int,
        phase: str = "Search",
        found_total: int = 0,
        known_identities: dict[str, str] | None = None,
    ) -> None:
        with self._lock:
            self.phase_name, self.total, self.current = "Search", max(1, total), 0
            self.found_total = max(0, found_total)
            self._found_keys.clear()
            self._known_identities = {
                key.casefold(): identity
                for key, identity in (known_identities or {}).items()
            }
            self._draw()

    def phase(self, phase: str) -> None:
        # Las fases son detalles internos: la interfaz muestra una sola búsqueda.
        return

    def found(self, *keys: str) -> None:
        normalized = [key.casefold() for key in keys if key]
        if not normalized:
            return
        with self._lock:
            if self._known_identities:
                identity = next(
                    (
                        self._known_identities[key]
                        for key in normalized
                        if key in self._known_identities
                    ),
                    "",
                )
                if not identity:
                    return
                self._found_keys.add(identity)
            else:
                self._found_keys.add(normalized[0])
            self._draw()

    def advance(self, amount: int = 1) -> None:
        with self._lock:
            self.current = min(self.total, self.current + amount)
            self._draw()

    def complete(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            self.current = self.total
            self._draw()
            self._clear_unlocked()

    def clear(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._clear_unlocked()

    def _clear_unlocked(self) -> None:
        if self._visible_width == 0:
            return
        self.stream.write("\r" + (" " * self._visible_width) + "\r")
        self.stream.flush()
        self._visible_width = 0

    def _draw(self) -> None:
        if not self.enabled:
            return
        ratio = self.current / self.total
        width = 24
        filled = round(width * ratio)
        bar = "█" * filled + "─" * (width - filled)
        line = (
            f"Search:    [{bar}] {ratio:>6.1%} {self.current}/{self.total}  "
            f"[founds: {len(self._found_keys)}/{self.found_total}]"
        )
        self._visible_width = max(self._visible_width, len(line))
        self.stream.write("\r" + line.ljust(self._visible_width))
        self.stream.flush()
