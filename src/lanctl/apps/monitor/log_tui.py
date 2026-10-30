"""Live, bounded operational-log viewer; closing it has no service side effects."""

from __future__ import annotations

import os
import shutil
import sys
import time
from collections import deque
from contextlib import contextmanager

from rich.console import Group
from rich.table import Table
from rich.text import Text

from lanctl.core.terminal_ui import ManagementScreen
from lanctl.shared.i18n import t


class LogViewModel:
    def __init__(self, limit=100, minimum=1):
        if (
            type(limit) is not int
            or not 1 <= limit <= 1000
            or type(minimum) is not int
            or not 1 <= minimum <= 59
        ):
            raise ValueError("limit debe estar entre 1-1000 y level entre 1-59")
        self.history = deque(maxlen=limit)
        self.minimum = minimum
        self.paused = False
        self.frozen = []
        self.query = ""
        self.editing = False
        self.offset = 0

    def ingest(self, rows):
        self.history.extend(rows)

    def rows(self, size):
        rows = self.frozen if self.paused else list(self.history)
        filtered = [
            r
            for r in reversed(rows)
            if (r["level"] is None or r["level"] >= self.minimum)
            and self.query.casefold() in r["message"].casefold()
        ]
        self.offset = min(self.offset, max(0, len(filtered) - 1))
        return filtered[self.offset : self.offset + size]

    def key(self, key, page_size=15):
        if self.editing:
            if key in {"\r", "\n", "\x1b"}:
                self.editing = False
            elif key in {"\b", "\x7f"}:
                self.query = self.query[:-1]
            elif len(key) == 1 and key.isprintable() and len(self.query) < 200:
                self.query += key
            self.offset = 0
            return True
        if key in {"q", "Q", "\x03", "\x04"}:
            return False
        if key in {"p", " "}:
            self.paused = not self.paused
            self.frozen = list(self.history) if self.paused else []
            self.offset = 0
        elif key in {"up", "down", "pageup", "pagedown"}:
            if not self.paused:
                self.paused = True
                self.frozen = list(self.history)
            delta = {"up": 1, "down": -1, "pageup": page_size, "pagedown": -page_size}[key]
            self.offset = max(0, min(len(self.frozen) - 1, self.offset + delta))
        elif key == "f":
            self.minimum = next((v for v in (1, 20, 30, 40, 50) if v > self.minimum), 1)
            self.offset = 0
        elif key == "/":
            self.query = ""
            self.editing = True
        return True


@contextmanager
def _keyboard():
    if os.name == "nt":
        import msvcrt

        def read():
            if not msvcrt.kbhit():
                return ""
            key = msvcrt.getwch()
            if key in {"\x00", "\xe0"}:
                return {"H": "up", "P": "down", "I": "pageup", "Q": "pagedown"}.get(
                    msvcrt.getwch(), ""
                )
            return key

        yield read
    else:
        import codecs
        import select
        import termios
        import tty

        descriptor = sys.stdin.fileno()
        previous = termios.tcgetattr(descriptor)
        decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        try:
            tty.setcbreak(descriptor)

            def read():
                if not select.select([descriptor], [], [], 0)[0]:
                    return ""
                byte = os.read(descriptor, 1)
                if not byte:
                    return "\x04"
                key = decoder.decode(byte)
                if key == "\x1b":
                    suffix = b""
                    while len(suffix) < 4 and select.select([descriptor], [], [], 0.01)[0]:
                        suffix += os.read(descriptor, 1)
                    return {b"[A": "up", b"[B": "down", b"[5~": "pageup", b"[6~": "pagedown"}.get(
                        suffix, key
                    )
                return key

            yield read
        finally:
            termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)


def follow_log_tui(*, limit=100, minimum=1):
    from lanctl.apps.monitor.log_stream import LogFollower, follow_logs
    from lanctl.core.config import load_config
    from lanctl.core.paths import application_path

    model = LogViewModel(limit, minimum)
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        return follow_logs(limit=limit, minimum=minimum)
    follower = LogFollower(application_path(load_config()["programLog"]), limit)
    try:
        with ManagementScreen() as screen, _keyboard() as read_key:
            while True:
                model.ingest(follower.poll())
                page_size = max(1, shutil.get_terminal_size((100, 30)).lines - 11)
                table = Table(title=t("LANCTL.MONITOR.LOG.TITLE"), expand=True)
                table.add_column("Archivo", no_wrap=True)
                table.add_column("Nivel", width=5)
                table.add_column("Mensaje")
                for row in model.rows(page_size):
                    level = row["level"] or 0
                    style = "bold red" if level >= 40 else "yellow" if level >= 20 else "cyan"
                    table.add_row(
                        Text(row["file"]),
                        str(row["level"] or "—"),
                        Text(row["message"], style=style),
                    )
                screen.draw(
                    Group(
                        table,
                        Text(
                            f"{'PAUSA' if model.paused else 'EN DIRECTO'} · nivel ≥{model.minimum} · filtro: {model.query} · {len(model.history)}/{limit} líneas"
                        ),
                        Text(
                            "P pausa · ↑/↓/RePág/AvPág historial · F nivel · / filtro, Enter aceptar · Q cerrar"
                        ),
                    )
                )
                if not model.key(read_key(), page_size):
                    return 0
                time.sleep(0.1)
    except KeyboardInterrupt:
        return 0
