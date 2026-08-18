import io
import unittest

from rich.text import Text

from app.tui_render import RichTuiRenderer


class RichTuiRendererTests(unittest.TestCase):
    def test_screen_renderer_uses_full_refresh_and_restores_cursor(self):
        stream = io.StringIO()
        renderer = RichTuiRenderer(stream)

        renderer.render_screen(
            ["\x1b[36mLANCTL\x1b[0m", "Inventario"],
            width=40,
            height=3,
            cursor_row=2,
            cursor_column=8,
        )

        output = stream.getvalue()
        self.assertTrue(output.startswith("\x1b[?25h\x1b[2J\x1b[H"))
        self.assertIn("LANCTL", output)
        self.assertIn("Inventario", output)
        self.assertTrue(output.endswith("\x1b[2;8H"))

    def test_progress_uses_rich_bar_and_reports_discoveries(self):
        output = RichTuiRenderer.progress_line(
            width=100,
            current=50,
            total=100,
            found=12,
            scanning=True,
        )

        self.assertIn("ESCANEO", output)
        self.assertIn("50.0%", output)
        self.assertIn("encontrados 12", output)
        self.assertEqual(Text.from_ansi(output).cell_len, 100)

    def test_progress_has_a_compact_fallback_for_narrow_terminals(self):
        output = RichTuiRenderer.progress_line(
            width=40,
            current=2,
            total=10,
            found=1,
            scanning=True,
        )

        self.assertIn("20%", output)
        self.assertEqual(Text.from_ansi(output).cell_len, 40)

    def test_modal_renderer_overlays_panel_and_hides_cursor(self):
        stream = io.StringIO()
        renderer = RichTuiRenderer(stream)

        renderer.render_modal(
            ["L" * 80] * 20,
            title="INFO",
            tabs=["Identidad", "Puertos"],
            selected_tab=1,
            body=["Puerto 22 SSH"],
            footer="Esc cerrar",
            width=80,
            height=20,
        )

        output = stream.getvalue()
        self.assertTrue(output.startswith("\x1b[?25l"))
        self.assertIn("INFO", output)
        self.assertIn("Puerto 22 SSH", output)
        visible_rows = output.removeprefix("\x1b[?25l\x1b[2J\x1b[H").splitlines()
        panel_rows = [row for row in visible_rows if "INFO" in row or "Puerto 22 SSH" in row]
        self.assertTrue(panel_rows)
        self.assertTrue(all(Text.from_ansi(row).cell_len == 80 for row in panel_rows))
        title_row = Text.from_ansi(next(row for row in panel_rows if "INFO" in row)).plain
        self.assertTrue(title_row.startswith("LL"))
        self.assertTrue(title_row.endswith("LL"))

    def test_modal_footer_renders_keys_as_keycaps(self):
        footer = RichTuiRenderer._modal_footer(
            "←/→ menú  ↑/↓ variable  Tab editar  Ctrl+S guardar  Esc cerrar"
        )

        key_spans = [span for span in footer.spans if "on bright_white" in str(span.style)]
        self.assertEqual(len(key_spans), 5)
        self.assertEqual(footer[key_spans[3].start : key_spans[3].end].plain, "Ctrl+S")


if __name__ == "__main__":
    unittest.main()
