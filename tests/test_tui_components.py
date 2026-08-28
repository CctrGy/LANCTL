import io

from rich.text import Text

from lanctl.apps.ip.interfaces.tui.controllers import ManagerController, SettingsEditor
from lanctl.apps.ip.interfaces.tui.keyboard import KEY_BINDINGS, read_windows_key
from lanctl.apps.ip.interfaces.tui.layout import adaptive_layout
from lanctl.apps.ip.interfaces.tui.modal import ModalState, SettingField
from lanctl.apps.ip.interfaces.tui.render import RichTuiRenderer


def test_adaptive_layout_snapshots() -> None:
    snapshots = [
        (40, 12, False, (True, 2, 38, 10, 3)),
        (80, 24, False, (False, 6, 74, 18, 11)),
        (160, 50, True, (False, 6, 130, 36, 29)),
    ]
    for width, height, settings, expected in snapshots:
        layout = adaptive_layout(width, height, settings=settings)
        assert (
            layout.compact,
            layout.modal_margin,
            layout.modal_width,
            layout.modal_height,
            layout.body_rows,
        ) == expected


def test_screen_snapshot_pads_every_row_and_erases_adjacent_residue() -> None:
    stream = io.StringIO()
    RichTuiRenderer(stream).render_screen(["LANCTL", "X" * 30], width=12, height=3)

    payload = stream.getvalue().removeprefix("\x1b[?25l\x1b[2J\x1b[H")
    rows = payload.splitlines()
    # Rich evita imprimir la última fila vacía y reserva una celda antes de un
    # salto de línea; el borrado completo inicial garantiza que ambas zonas
    # queden limpias sin provocar autowrap sobre la fila adyacente.
    assert [Text.from_ansi(row).plain for row in rows] == [
        "LANCTL      ",
        "XXXXXXXXXXXX",
    ]
    assert all(Text.from_ansi(row).cell_len <= 12 for row in rows)


def test_keyboard_bindings_and_windows_decoder_share_semantic_names() -> None:
    values = iter(("\xe0", "A"))
    assert read_windows_key(lambda: next(values)) == "F7"
    assert KEY_BINDINGS["F7"] == "Plugins"


def test_settings_editor_snapshot_and_manager_navigation() -> None:
    fields = [
        SettingField("workers", "Workers", "--workers", "64", "32", "entero", "RED"),
        SettingField("timeout", "Timeout", "--timeout", "1", "1", "segundos", "RED"),
    ]
    modal = ModalState("settings", "SETTINGS", ["RED"], [[]], items=fields)
    page = SettingsEditor.render_page(modal)
    assert page[:4] == [
        "  CAMPO                      VALOR                         FORMATO",
        "  ─────────────────────────  ─────────────────────────────  ─────────────────────────",
        "▶* Workers                   64                            entero",
        "   Timeout                   1                             segundos",
    ]

    manager = ModalState("plugins", "PLUGIN", ["Plugins"], [["uno", "dos"]])
    changes = []
    ManagerController.move(manager, 1, lambda state: changes.append(state.selected))
    assert (manager.selected, manager.scroll, changes) == (1, 0, [1])
