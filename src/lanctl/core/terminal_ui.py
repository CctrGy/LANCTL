"""Small synchronous full-screen host for management consoles."""

from __future__ import annotations

import io
import shutil
import sys

from rich.console import Console


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
