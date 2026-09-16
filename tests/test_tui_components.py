import io

from rich.text import Text

from lanctl.apps.ip.interfaces.tui.controllers import ManagerController, SettingsEditor
from lanctl.apps.ip.interfaces.tui.keyboard import KEY_BINDINGS, read_windows_key
from lanctl.apps.ip.interfaces.tui.layout import (
    adaptive_layout,
    allocate_column_widths,
    normalize_cli_percent,
    normalize_column_specs,
    normalize_panel_layout,
    panel_rows,
)
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


def test_panel_layout_and_vertical_proportion_are_bounded() -> None:
    assert normalize_panel_layout("cli_arriba") == "cli.top"
    assert normalize_panel_layout("cli_abajo") == "cli.bottom"
    assert panel_rows(60, 30) == (41, 18)
    assert normalize_cli_percent("15%") == 15


def test_column_allocator_keeps_ip_and_mac_fixed_and_fills_available_width() -> None:
    fields = ("IP", "responseMs", "cnf", "ALIAS", "MAC", "NAME", "GROUP", "description")
    widths = allocate_column_widths(
        fields,
        available=158,
        gap=2,
        specs={"GROUP": "20%", "description": "25%"},
    )
    assert widths["IP"] == 15
    assert widths["MAC"] == 17
    assert widths["GROUP"] >= 5
    assert sum(widths.values()) + 2 * (len(fields) - 1) == 158


def test_fixed_columns_reject_percentage_customization() -> None:
    try:
        normalize_column_specs({"IP": "20%"})
    except ValueError as error:
        assert "15ch" in str(error)
    else:
        raise AssertionError("IP no debe aceptar una anchura porcentual")


def test_legacy_protocol_column_weight_migrates_to_users() -> None:
    specs = normalize_column_specs({"protocols": "14%"})
    assert specs["users"] == "14%"
    assert "protocols" not in specs


def test_screen_snapshot_pads_every_row_and_erases_adjacent_residue() -> None:
    stream = io.StringIO()
    RichTuiRenderer(stream).render_screen(["LANCTL", "X" * 30], width=12, height=3)

    payload = stream.getvalue().removeprefix("\x1b[?25l\x1b[H")
    rows = payload.splitlines()
    # Rich evita imprimir la última fila vacía y reserva una celda antes de un
    # salto de línea. Cada fila emitida cubre el frame anterior sin provocar
    # autowrap sobre la fila adyacente.
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
    assert "CAMPO" in page[0] and "VALOR" in page[0] and "FORMATO" in page[0]
    assert "▶* Workers" in page[2] and "64" in page[2] and "entero" in page[2]
    assert "Timeout" in page[3] and "1" in page[3] and "segundos" in page[3]

    manager = ModalState("plugins", "PLUGIN", ["Plugins"], [["uno", "dos"]])
    changes = []
    ManagerController.move(manager, 1, lambda state: changes.append(state.selected))
    assert (manager.selected, manager.scroll, changes) == (1, 0, [1])


def test_settings_editor_adapts_rows_to_narrow_cell_width() -> None:
    fields = [
        SettingField(
            "language",
            "Idioma 日本語",
            "--language",
            "español",
            "en",
            "texto Unicode",
            "GENERAL",
        )
    ]
    modal = ModalState("settings", "SETTINGS", ["GENERAL"], [[]], items=fields)

    page = SettingsEditor.render_page(modal, table_width=32, description_width=28)

    assert "CAMPO / VALOR / FORMATO" in page[0]
    assert all(Text(row).cell_len <= 32 for row in page[:5])
