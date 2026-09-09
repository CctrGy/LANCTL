"""Renderizado Rich sobre StringIO para una pantalla ANSI completa."""

from __future__ import annotations

import io
from typing import TextIO

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.text import Text


class RichTuiRenderer:
    def __init__(self, stream: TextIO) -> None:
        self.stream = stream
        self._last_size: tuple[int, int] | None = None

    @staticmethod
    def _console(target: TextIO, width: int, height: int | None = None) -> Console:
        return Console(
            file=target,
            force_terminal=True,
            color_system="standard",
            width=max(1, width),
            height=height,
            legacy_windows=False,
            highlight=False,
            soft_wrap=True,
        )

    def render(
        self,
        upper: RenderableType,
        lower: RenderableType,
        footer: RenderableType,
        *,
        width: int,
        height: int,
        upper_height: int,
        lower_height: int,
        cursor_row: int | None = None,
        cursor_column: int | None = None,
        modal: RenderableType | None = None,
        modal_title: str = "INFO",
        modal_size: tuple[int, int] | None = None,
    ) -> None:
        """Genera el frame entero en memoria y lo vuelca en una sola escritura."""
        buffer = io.StringIO()
        console = self._console(buffer, width, height)
        lines = [separator_line("INFO", width)]
        lines.extend(self._fixed_rows(upper, width, upper_height - 1))
        lines.append(separator_line("CLI", width))
        lines.extend(self._fixed_rows(lower, width, lower_height - 1))
        lines.extend(self._fixed_rows(footer, width, 1))
        if modal is not None:
            lines = self._overlay_modal(
                lines[:height], modal, modal_title, width, height, modal_size
            )
        console.print(*lines[:height], sep="\n", end="")
        visible = modal is None and cursor_row is not None and cursor_column is not None
        cursor = f"\x1b[{cursor_row};{cursor_column}H" if visible else ""
        size = (width, height)
        repaint = "\x1b[2J\x1b[H" if self._last_size not in (None, size) else "\x1b[H"
        self.stream.write(
            ("\x1b[?25h" if visible else "\x1b[?25l") + repaint + buffer.getvalue() + cursor
        )
        self.stream.flush()
        self._last_size = size

    @classmethod
    def _overlay_modal(
        cls,
        screen: list[Text],
        body: RenderableType,
        title: str,
        width: int,
        height: int,
        requested_size: tuple[int, int] | None = None,
    ) -> list[Text]:
        """Superpone una ventana virtual Rich sobre el frame congelado."""
        modal_width, modal_height = requested_size or cls.modal_size(body, title, width, height)
        panel = Panel(
            body,
            title=f"[bold bright_cyan] INFO · {title} [/]",
            subtitle=modal_footer(),
            border_style="bright_cyan",
            width=modal_width,
            height=modal_height,
            padding=(1, 2),
        )
        buffer = io.StringIO()
        cls._console(buffer, modal_width, modal_height).print(panel, end="")
        overlay = [Text.from_ansi(line) for line in buffer.getvalue().splitlines()]
        top = max(0, (height - len(overlay)) // 2)
        left = max(0, (width - modal_width) // 2)
        result = [row.copy() for row in screen]
        while len(result) < height:
            result.append(Text(" " * width))
        for offset, overlay_row in enumerate(overlay):
            if top + offset >= height:
                break
            base = result[top + offset]
            base.truncate(width, pad=True)
            overlay_row.truncate(modal_width, overflow="crop", pad=True)
            combined = base[:left]
            combined.append_text(overlay_row)
            combined.append_text(base[left + modal_width : width])
            combined.truncate(width, pad=True)
            result[top + offset] = combined
        return result

    @staticmethod
    def modal_size(body: RenderableType, title: str, width: int, height: int) -> tuple[int, int]:
        """Ajusta el modal al contenido sin superar la terminal actual."""
        if isinstance(body, Text):
            rows = list(body.split("\n"))
            content_width = max((row.cell_len for row in rows), default=0)
            content_height = max(1, len(rows))
        else:
            plain = str(body).splitlines() or [""]
            content_width = max(map(len, plain))
            content_height = len(plain)
        footer_width = modal_footer().cell_len + 4
        title_width = len(f" INFO · {title} ") + 6
        modal_width = min(max(28, width - 4), max(34, content_width + 6, footer_width, title_width))
        modal_height = min(max(6, height - 4), max(5, content_height + 4))
        return modal_width, modal_height

    @classmethod
    def _fixed_rows(cls, renderable: RenderableType, width: int, height: int) -> list[Text]:
        """Convierte contenido Rich en un rectángulo sin bordes laterales."""
        if isinstance(renderable, Text):
            rows = list(renderable.split("\n"))
        else:
            rows = [
                Text.from_ansi(line) for line in cls.render_to_text(renderable, width).splitlines()
            ]
        output: list[Text] = []
        for source in rows[: max(0, height)]:
            row = source.copy()
            row.no_wrap = True
            row.overflow = "crop"
            row.truncate(width, overflow="crop", pad=True)
            output.append(row)
        while len(output) < height:
            output.append(Text(" " * width))
        return output

    @classmethod
    def render_to_text(cls, renderable: RenderableType, width: int) -> str:
        buffer = io.StringIO()
        cls._console(buffer, width).print(renderable, end="")
        return buffer.getvalue()


def separator_line(title: str, width: int) -> Text:
    """Separador horizontal exclusivamente ASCII, sin bordes verticales."""
    label = f"-------[ {title.upper()} ]"
    return Text(label + "-" * max(0, width - len(label)), style="bright_black")


def modal_footer() -> Text:
    """Pie de ventana virtual con teclas resaltadas como keycaps."""
    text = Text()
    key_style = "bold black on bright_cyan"
    text.append(" ↑/↓ ", style=key_style)
    text.append(" desplazar", style="bright_white")
    text.append("   ")
    text.append(" Tab ", style=key_style)
    text.append(" editar", style="bright_white")
    text.append("   ")
    text.append(" F2 ", style=key_style)
    text.append(" / ", style="bright_white")
    text.append(" Esc ", style=key_style)
    text.append(" cerrar", style="bright_white")
    return text


def footer_bar(width: int) -> Text:
    text = Text()
    actions = (
        ("↑↓", "Seleccionar"),
        ("Enter", "Abrir/Ejecutar"),
        ("PgUp/PgDn", "CLI"),
        ("Esc", "Salir"),
    )
    for index, (key, label) in enumerate(actions):
        if index:
            text.append("  ")
        text.append(f" {key} ", style="bold black on bright_white")
        text.append(f" {label}", style="white on black")
    text.truncate(max(1, width), pad=True)
    return text
