"""Small synchronous full-screen host for management consoles."""

from __future__ import annotations

import io
import shutil
import sys
from contextlib import contextmanager

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from lanctl.shared.i18n import t


@contextmanager
def _viewer_keyboard():
    """Immediate navigation keys; restore the terminal even after an error."""
    if sys.platform == "win32":
        import msvcrt

        def read():
            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                return {
                    "H": "UP",
                    "P": "DOWN",
                    "I": "PGUP",
                    "Q": "PGDN",
                    "G": "HOME",
                    "O": "END",
                }.get(msvcrt.getwch(), "")
            return "CLOSE" if key in ("\r", "\x1b", "\x03", "q", "Q") else ""

        yield read
    else:
        import os
        import select
        import termios
        import tty

        descriptor = sys.stdin.fileno()
        previous = termios.tcgetattr(descriptor)

        def read():
            key = os.read(descriptor, 1)
            if key != b"\x1b":
                return "CLOSE" if key in (b"", b"\r", b"\n", b"q", b"Q", b"\x03", b"\x04") else ""
            sequence = b""
            while len(sequence) < 8 and select.select([descriptor], [], [], 0.05)[0]:
                sequence += os.read(descriptor, 1)
                if sequence in (
                    b"[A",
                    b"[B",
                    b"[5~",
                    b"[6~",
                    b"[H",
                    b"[F",
                    b"OH",
                    b"OF",
                    b"[1~",
                    b"[4~",
                ):
                    break
            return {
                b"[A": "UP",
                b"[B": "DOWN",
                b"[5~": "PGUP",
                b"[6~": "PGDN",
                b"[H": "HOME",
                b"OH": "HOME",
                b"[1~": "HOME",
                b"[F": "END",
                b"OF": "END",
                b"[4~": "END",
            }.get(sequence, "CLOSE" if not sequence else "")

        try:
            tty.setcbreak(descriptor)
            current = termios.tcgetattr(descriptor)
            current[0] &= ~(termios.IXON | termios.IXOFF)
            termios.tcsetattr(descriptor, termios.TCSADRAIN, current)
            yield read
        finally:
            termios.tcsetattr(descriptor, termios.TCSADRAIN, previous)


class ManagementScreen:
    """Render one padded frame per interaction, without erase-before-repaint."""

    def __enter__(self):
        self.active = sys.stdout.isatty() and sys.stdin.isatty()
        if self.active:
            sys.stdout.write("\x1b[?1049h\x1b[H")
            sys.stdout.flush()
        return self

    def draw(self, content):
        width, height = shutil.get_terminal_size((100, 30))
        buffer = io.StringIO()
        console = Console(
            file=buffer, width=width, force_terminal=self.active, highlight=False, markup=False
        )
        if self.active:
            lines = console.render_lines(
                content, console.options.update(width=width, height=max(1, height - 4)), pad=True
            )

            for line in lines[: max(1, height - 4)]:
                for segment in line:
                    console.print(segment.text, style=segment.style, end="", soft_wrap=True)
                console.print()
            for _ in range(max(0, height - 4 - len(lines))):
                console.print(" " * width)
            # The frame and cursor positioning are emitted together.
            sys.stdout.write("\x1b[H" + buffer.getvalue() + "\x1b[J")
            sys.stdout.flush()
        else:
            console.print(content)
            sys.stdout.write(buffer.getvalue())

    def __exit__(self, *_exc):
        if self.active:
            sys.stdout.write("\x1b[?1049l\x1b[?25h")
            sys.stdout.flush()

    def show_text(self, value, *, title=t("LANCTL.UI.TEXT.HELP")):
        """Scrollable read-only view inside the current alternate screen."""
        if not self.active:
            self.draw(Panel(Text.from_ansi(value), title=title))
            input(t("LANCTL.UI.SCREEN.PRESS_ENTER_TO_RETURN_TO_THE_PANEL"))
            return
        offset = 0
        with _viewer_keyboard() as read:
            while True:
                width, height = shutil.get_terminal_size((100, 30))
                rows = max(1, height - 9)
                console = Console(file=io.StringIO(), width=max(1, width - 4))
                lines = Text.from_ansi(value).wrap(console, max(1, width - 4))
                maximum = max(0, len(lines) - rows)
                offset = min(offset, maximum)
                body = Text("\n").join(lines[offset : offset + rows])
                self.draw(
                    Panel(
                        body,
                        title=title,
                        subtitle=t(
                            "LANCTL.UI.MESSAGE.VALUE_VALUE_VALUE_PGUP_PGDN_HOME_END_ESC_ENTER_BACK",
                            value0=f"{offset + 1}",
                            value1=f"{min(offset + rows, len(lines))}",
                            value2=f"{len(lines)}",
                        ),
                    )
                )
                key = read()
                if key == "CLOSE":
                    return
                if key == "HOME":
                    offset = 0
                elif key == "END":
                    offset = maximum
                else:
                    offset = max(
                        0,
                        min(
                            maximum,
                            offset + {"UP": -1, "DOWN": 1, "PGUP": -rows, "PGDN": rows}.get(key, 0),
                        ),
                    )

    @contextmanager
    def suspended(self):
        """Give nested interactive programs native streams and their own screen."""
        if self.active:
            sys.stdout.write("\x1b[?1049l\x1b[?25h")
            sys.stdout.flush()
        try:
            yield
        finally:
            if self.active:
                sys.stdout.write("\x1b[?1049h\x1b[H")
                sys.stdout.flush()
