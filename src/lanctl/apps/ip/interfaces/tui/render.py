from __future__ import annotations

import io
import re
from collections.abc import Iterable
from typing import TextIO

from rich.console import Console
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.text import Text


class RichTuiRenderer:
    """Adaptador de Rich para la pantalla completa de LANCTL.

    El TUI conserva su modelo de entrada y navegación. Este adaptador se ocupa
    exclusivamente de convertir las filas visuales en una pantalla ANSI
    consistente y de dibujar componentes gráficos como el progreso.
    """

    def __init__(self, stream: TextIO) -> None:
        self.stream = stream

    @staticmethod
    def _console(target: TextIO, width: int) -> Console:
        return Console(
            file=target,
            force_terminal=True,
            color_system="standard",
            width=max(1, width),
            legacy_windows=False,
            highlight=False,
            soft_wrap=True,
        )

    def render_screen(
        self,
        lines: Iterable[str],
        *,
        width: int,
        height: int,
        cursor_row: int | None = None,
        cursor_column: int | None = None,
    ) -> None:
        """Repinta una pantalla mediante Rich y posiciona después el cursor."""

        buffer = io.StringIO()
        console = self._console(buffer, width)
        rendered_lines: list[Text] = []
        for source in list(lines)[:height]:
            text = source.copy() if isinstance(source, Text) else Text.from_ansi(source)
            text.no_wrap = True
            text.overflow = "crop"
            rendered_lines.append(text)
        while len(rendered_lines) < height:
            rendered_lines.append(Text())
        console.print(*rendered_lines, sep="\n", end="")

        cursor_visible = cursor_row is not None and cursor_column is not None
        prefix = "\x1b[?25h" if cursor_visible else "\x1b[?25l"
        suffix = f"\x1b[{cursor_row};{cursor_column}H" if cursor_visible else ""
        self.stream.write(prefix + "\x1b[2J\x1b[H" + buffer.getvalue() + suffix)
        self.stream.flush()

    def render_modal(
        self,
        background: Iterable[str],
        *,
        title: str,
        tabs: list[str],
        selected_tab: int,
        body: Iterable[str],
        footer: str,
        width: int,
        height: int,
        max_width: int = 100,
        max_height: int = 30,
    ) -> None:
        """Superpone un panel centrado sobre una captura inmóvil del TUI."""

        screen = list(background)[:height]
        while len(screen) < height:
            screen.append("")
        modal_width = max(10, min(max(10, width - 6), max_width))
        modal_height = max(6, min(max(6, height - 6), max_height))
        tab_line = Text()
        for index, label in enumerate(tabs):
            if index:
                tab_line.append("  ")
            tab_line.append(
                f" {label} ",
                style="bold black on bright_cyan" if index == selected_tab else "cyan",
            )
        content = Text()
        content.append_text(tab_line)
        content.append("\n" + "─" * max(1, modal_width - 6), style="bright_black")
        for line in body:
            content.append("\n")
            content.append_text(self._modal_line(str(line)))
        panel = Panel(
            content,
            title=f"[bold bright_cyan]{title}[/]",
            subtitle=self._modal_footer(footer),
            border_style="bright_cyan",
            width=modal_width,
            height=modal_height,
            padding=(0, 1),
        )
        buffer = io.StringIO()
        console = self._console(buffer, modal_width)
        console.print(panel, end="")
        overlay = buffer.getvalue().splitlines()
        top = max(0, (height - len(overlay)) // 2)
        left = max(0, (width - modal_width) // 2)
        for offset, line in enumerate(overlay):
            if top + offset < height:
                # Sustituye únicamente el rectángulo del modal. Los segmentos
                # laterales proceden de la captura congelada y conservan sus
                # estilos; dentro del rectángulo, Panel ya rellena cada celda.
                frozen = Text.from_ansi(str(screen[top + offset]))
                frozen.truncate(width, pad=True)
                panel_row = Text.from_ansi(line)
                panel_row.truncate(modal_width, pad=True)
                row = frozen[:left]
                row.append_text(panel_row)
                row.append_text(frozen[left + modal_width : width])
                row.truncate(width, pad=True)
                screen[top + offset] = row
        self.render_screen(screen, width=width, height=height)

    @staticmethod
    def _modal_footer(source: str) -> Text:
        footer = Text(source, style="bright_black")
        # Las teclas se presentan como keycaps, igual que en la barra inferior
        # del TUI. El orden largo-a-corto evita partir Ctrl+R como una tecla R.
        footer.highlight_regex(
            re.compile(
                r"(?<!\w)(?:Shift\+Tab|Ctrl\+[A-Z]|RePag|AvPag|Enter|Esc|Tab|F\d{1,2}|←/→|↑/↓|↑↓)(?!\w)"
            ),
            style="bold black on bright_white",
        )
        return footer

    @staticmethod
    def _modal_line(source: str) -> Text:
        """Da jerarquía visual al contenido sin acoplar Rich al modelo TUI."""

        line = Text.from_ansi(source)
        plain = line.plain
        stripped = plain.strip()
        if not stripped:
            return line
        if stripped.startswith(("▶", "◆")):
            line.stylize("bold bright_cyan")
        elif stripped == "DESCRIPCIÓN":
            line.stylize("bold bright_yellow")
        elif stripped.startswith(("├", "└", "│")) or "──" in stripped:
            line.stylize("cyan")
        elif ":" in plain:
            separator = plain.index(":")
            line.stylize("bold cyan", 0, separator + 1)
        for state, style in (
            ("ENABLED", "bold green"),
            ("DISABLED", "bright_black"),
            ("BLOCKED", "bold yellow"),
            ("ERROR", "bold red"),
            ("INCOMPATIBLE", "bold red"),
        ):
            start = plain.find(state)
            if start >= 0:
                line.stylize(style, start, start + len(state))
        return line

    @classmethod
    def progress_line(
        cls,
        *,
        width: int,
        current: int,
        total: int,
        found: int,
        scanning: bool,
    ) -> str:
        """Construye la barra de búsqueda con el componente ProgressBar de Rich."""

        total = max(1, total)
        current = max(0, min(current, total))
        ratio = current / total
        content_width = max(20, round(width * 0.90))
        left_margin = max(0, (width - content_width) // 2)
        right_margin = max(0, width - content_width - left_margin)
        state = "ESCANEO" if scanning else "COMPLETADO"
        state_style = "bold yellow" if scanning else "bold green"
        metrics = (
            f"{ratio:6.1%} {current}/{total} | encontrados {found}"
            if content_width >= 60
            else f"{ratio:.0%} {current}/{total} | {found}"
        )
        bar_width = max(1, content_width - len(state) - len(metrics) - 3)

        bar_buffer = io.StringIO()
        bar_console = cls._console(bar_buffer, bar_width)
        bar_console.print(
            ProgressBar(
                total=total,
                completed=current,
                width=bar_width,
                complete_style="green" if not scanning else "yellow",
                finished_style="green",
                pulse_style="yellow",
            ),
            end="",
        )
        rendered_bar = bar_buffer.getvalue().splitlines()
        if rendered_bar:
            bar_line = rendered_bar[0]
        else:
            # Rich omite ProgressBar cuando la consola es más estrecha que su
            # ancho mínimo. El TUI debe seguir funcionando en 80 columnas y
            # sesiones SSH, por lo que se usa una barra compacta equivalente.
            completed = max(0, min(bar_width, round(bar_width * ratio)))
            bar_line = "█" * completed + "─" * (bar_width - completed)
        missing_bar_cells = bar_width - Text.from_ansi(bar_line).cell_len
        if missing_bar_cells > 0:
            bar_line += " " * missing_bar_cells
        row = Text(state, style=state_style)
        row.append(" ")
        row.append_text(Text.from_ansi(bar_line))
        row.append(" ")
        row.append(metrics, style=state_style)
        buffer = io.StringIO()
        console = cls._console(buffer, content_width)
        console.print(row, end="")
        line = buffer.getvalue().splitlines()[0] if buffer.getvalue() else ""
        # Rich puede calcular una cuadrícula más estrecha que el ancho solicitado
        # cuando todas sus columnas tienen contenido de ancho fijo. La barra vive
        # en una fila completa del ListElement, así que completamos el margen sin
        # contar las secuencias ANSI como celdas visibles.
        visible_width = Text.from_ansi(line).cell_len
        if visible_width < content_width:
            line += " " * (content_width - visible_width)
        return " " * left_margin + line + " " * right_margin
