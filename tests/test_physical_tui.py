import io
import os
import tempfile
import unittest
from itertools import pairwise
from pathlib import Path
from unittest.mock import patch

from lanctl.apps.wire.cli.commands import CommandProcessor
from lanctl.apps.wire.idf.database import IDFDatabaseManager
from lanctl.apps.wire.idf.sample_topology import seed_sample_topology
from lanctl.apps.wire.tui.app import LanwreTui
from lanctl.apps.wire.tui.detail import (
    combine_with_sidebar,
    element_detail,
    element_sidebar,
    selectable_ports,
)
from lanctl.apps.wire.tui.editor import connection_browser_view, editable_fields, editor_view
from lanctl.apps.wire.tui.keyboard import decode_windows_key
from lanctl.apps.wire.tui.renderer import (
    RichTuiRenderer,
    detail_modal_footer,
    footer_bar,
    modal_footer,
    separator_line,
)


class TuiFoundationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name) / "idf.db"

    def tearDown(self):
        self.temporary.cleanup()

    def test_layout_auto_adjusts_to_height(self):
        self.assertEqual(LanwreTui.panel_heights(30), (17, 12))
        self.assertEqual(sum(LanwreTui.panel_heights(16)), 15)

    def test_command_processor_is_shared_with_external_cli(self):
        processor = CommandProcessor(IDFDatabaseManager(self.path))
        self.assertEqual(processor.execute("add sw").lines, ("Creado SW-00",))
        self.assertIn("SW-00", processor.execute("list").lines[0])

    def test_new_profile_is_visible_as_type_in_inventory(self):
        database = IDFDatabaseManager(self.path)
        processor = CommandProcessor(database)
        processor.execute("idf new SW -type switch.5Ports")
        processor.execute("idf add SW-01 -alias Core")
        tui = LanwreTui(self.path, stream=io.StringIO())
        self.assertIn("switch.5Ports", tui.tree_view(10, 120).plain)

    def test_tui_builds_tree_and_cli_views(self):
        database = IDFDatabaseManager(self.path)
        database.add("AP-01", {"zone": "office"})
        tui = LanwreTui(self.path, stream=io.StringIO())
        self.assertIn("AP-01", tui.tree_view(10).plain)
        self.assertIn("lanwire>", tui.cli_view(8).plain)

    def test_selected_inventory_keeps_column_colors_and_single_space_gaps(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "RT-00", {"type": "device.router", "name": "OTG", "description": "Toma de WLAN"}
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        table = tui.tree_view(10, 100)
        self.assertIn("▶ RT-00", table.plain)
        self.assertNotIn("│", table.plain)
        self.assertIn("─", table.plain.splitlines()[1])
        styles = {str(span.style) for span in table.spans}
        self.assertIn("bright_blue on grey50", styles)
        self.assertIn("bright_yellow on grey50", styles)
        self.assertIn("green on grey50", styles)
        selected_spans = [span for span in table.spans if "on grey50" in str(span.style)]
        self.assertTrue(
            all(right.start - left.end == 1 for left, right in pairwise(selected_spans))
        )
        self.assertIn("black on grey50", styles)
        self.assertTrue(all(len(line) <= 40 for line in tui.tree_view(10, 40).plain.splitlines()))

    def test_tab_cycles_between_element_wire_and_all_inventories(self):
        database = IDFDatabaseManager(self.path)
        database.add("SW-01", {"type": "device.switch"})
        database.add("WL-01", {"type": "wire", "kind": "wire.copper"})
        tui = LanwreTui(self.path, stream=io.StringIO())
        self.assertEqual([record["id"] for record in tui.records], ["SW-01"])
        tui.handle_key("TAB")
        self.assertEqual(tui.list_kind, "wires")
        self.assertEqual([record["id"] for record in tui.records], ["WL-01"])
        tui.handle_key("TAB")
        self.assertEqual(tui.list_kind, "all")
        self.assertEqual({record["id"] for record in tui.records}, {"SW-01", "WL-01"})
        tui.handle_key("TAB")
        self.assertEqual(tui.list_kind, "elements")
        self.assertEqual([record["id"] for record in tui.records], ["SW-01"])

    def test_new_fiber_prefix_appears_in_wire_inventory(self):
        database = IDFDatabaseManager(self.path)
        database.create("fb")
        tui = LanwreTui(self.path, stream=io.StringIO())
        self.assertNotIn("FB-00", [record["id"] for record in tui.records])
        tui.handle_key("TAB")
        self.assertIn("FB-00", [record["id"] for record in tui.records])
        self.assertEqual(tui.records[0]["data"]["kind"], "wire.fiber")

    def test_editor_separates_element_template_and_selected_port(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "SW-01",
            {
                "type": "device.switch",
                "ports": {"X1": {"kind": "wire.copper", "poe": False}},
            },
        )
        fields = editable_fields(database.get("SW-01"), "X1")
        view = editor_view(fields, 0).plain
        self.assertIn("DATOS DEL ELEMENTO", view)
        self.assertIn("PUERTOS · PLANTILLA COMÚN", view)
        self.assertIn("PUERTO · X1 · EXCEPCIÓN", view)

    def test_port_detail_hides_internal_gender_and_only_shows_enabled_poe(self):
        record = {
            "id": "SW-01",
            "data": {"type": "device.switch", "ports": {"X1": {"kind": "wire.copper"}}},
        }
        hidden = element_sidebar(record, [record], selected_port="X1").plain
        self.assertNotIn("gender", hidden.casefold())
        self.assertNotIn("POE", hidden)
        record["data"]["ports"]["X1"]["poe"] = True
        shown = element_sidebar(record, [record], selected_port="X1").plain
        self.assertIn("POE", shown)

    def test_delete_key_confirms_then_deletes_selected_element_and_disconnects_wires(self):
        database = IDFDatabaseManager(self.path)
        database.add("SW-01", {"type": "device.switch", "ports": {"X1": {}}})
        database.add(
            "WL-01",
            {"type": "wire", "endpoints": [{"device": "SW-01", "port": "X1"}]},
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.handle_key("DELETE")
        self.assertEqual(tui.utility_modal, "delete")
        tui.handle_key("ENTER")
        self.assertIsNone(database.get("SW-01"))
        self.assertEqual(database.get("WL-01")["data"]["endpoints"], [])

    def test_element_options_include_delete_with_confirmation(self):
        database = IDFDatabaseManager(self.path)
        database.add("SW-01", {"type": "device.switch", "ports": {"X1": {}}})
        database.add("WL-01", {"type": "wire", "endpoints": [{"device": "SW-01", "port": "X1"}]})
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-01"
        tui.modal_focus = "menu"
        self.assertEqual(tui._menu_count(), 7)
        tui.dimensions = lambda: (120, 30)
        tui.render()
        self.assertIn("Eliminar elemento", tui.stream.getvalue())
        tui.menu_selection = 3
        tui.handle_key("ENTER")
        self.assertEqual(tui.utility_modal, "delete")
        self.assertEqual(tui.delete_confirmation_id, "SW-01")
        tui.handle_key("ESC")
        self.assertIsNotNone(database.get("SW-01"))
        tui.handle_key("ENTER")
        tui.handle_key("ENTER")
        self.assertIsNone(database.get("SW-01"))
        self.assertEqual(database.get("WL-01")["data"]["endpoints"], [])

    def test_delete_option_works_without_a_selected_port(self):
        database = IDFDatabaseManager(self.path)
        database.add("SW-01", {"type": "device.switch", "ports": {}})
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-01"
        tui.modal_focus = "menu"
        tui.menu_selection = 3
        tui.handle_key("ENTER")
        self.assertEqual(tui.delete_confirmation_id, "SW-01")
        tui.handle_key("ENTER")
        self.assertIsNone(database.get("SW-01"))

    def test_title_opens_general_editor_and_cable_selector_excludes_full_wires(self):
        database = IDFDatabaseManager(self.path)
        database.add("SW-01", {"type": "device.switch", "ports": {"X1": {"kind": "wire.copper"}}})
        database.add("WL-01", {"type": "wire", "kind": "wire.copper", "endpoints": []})
        database.add(
            "WL-02",
            {
                "type": "wire",
                "kind": "wire.copper",
                "endpoints": [{"device": "AA-01", "port": "X1"}, {"device": "BB-01", "port": "X1"}],
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-01"
        tui.handle_key("UP")
        self.assertEqual(tui.modal_selection, -1)
        tui.handle_key("ENTER")
        self.assertEqual(tui.modal_focus, "menu")
        tui.handle_key("ENTER")
        self.assertEqual(tui.modal_focus, "editor")
        tui.handle_key("TAB")
        tui.handle_key("TAB")
        tui.handle_key("DOWN")
        self.assertEqual(tui.modal_selection, 0)
        tui.handle_key("TAB")
        tui.handle_key("DOWN")
        tui.handle_key("DOWN")
        tui.handle_key("ENTER")
        self.assertEqual(tui.action_option_index, 0)
        self.assertEqual(tui._available_cables_for_selected_port(), ("WL-01",))
        tui.handle_key("ENTER")
        self.assertEqual(
            database.get("WL-01")["data"]["endpoints"], [{"device": "SW-01", "port": "X1"}]
        )

    def test_windows_extended_key_is_decoded(self):
        keys = iter(("\xe0", "H"))
        self.assertEqual(decode_windows_key(lambda: next(keys)), "UP")
        keys = iter(("\x00", "="))
        self.assertEqual(decode_windows_key(lambda: next(keys)), "F3")

    def test_ascii_separator_has_no_vertical_borders(self):
        separator = separator_line("CLI", 40).plain
        self.assertEqual(separator, " CLI " + "─" * 35)
        self.assertNotIn("│", separator)

    def test_modal_footer_renders_padded_colored_keycaps(self):
        footer = modal_footer()
        self.assertEqual(footer.plain, " ↑/↓  desplazar    Tab  opciones    Esc  volver")
        self.assertEqual(footer.spans[0].style, "bold black on bright_cyan")

    def test_detail_footer_shows_f3_and_fits_narrow_terminals(self):
        wide = detail_modal_footer(120)
        narrow = detail_modal_footer(40)
        self.assertIn("F3  seguir", wide.plain)
        self.assertIn("Tab", wide.plain)
        self.assertIn("F3", narrow.plain)
        self.assertLess(narrow.cell_len + 4, 40)

    def test_f3_is_visible_in_wire_and_device_windows_only(self):
        database = IDFDatabaseManager(self.path)
        database.add("RT-00", {"type": "device.router", "ports": {"LAN1": {"kind": "wire.copper"}}})
        database.add(
            "WE-00",
            {
                "type": "wire",
                "kind": "wire.copper",
                "endpoints": [{"device": "RT-00", "port": "LAN1"}],
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.dimensions = lambda: (100, 28)
        for identifier in ("RT-00", "WE-00"):
            tui._open_detail(identifier)
            tui.stream = io.StringIO()
            tui.renderer.stream = tui.stream
            tui.render()
            self.assertIn("F3", tui.stream.getvalue())
        tui.handle_key("ESC")
        tui.handle_key("F9")
        self.assertNotIn("F3", tui._utility_modal_content()[1].plain)

    def test_footer_prioritizes_essential_actions_and_expands_when_space_allows(self):
        narrow = footer_bar(58).plain
        wide = footer_bar(180).plain
        for key in ("F1", "Esc"):
            self.assertIn(key, narrow)
        self.assertNotIn("Ctrl+J", narrow)
        for key in ("F12", "Ctrl+S", "F7", "F9", "Ctrl+C", "Ctrl+J", "Ctrl+H"):
            self.assertIn(key, wide)

    def test_cursor_points_to_end_of_real_prompt(self):
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.command = "abc"
        tui.command_cursor = 3
        tui.dimensions = lambda: (80, 20)
        tui.render()
        upper_height, _ = tui._panel_heights(20)
        expected_row = upper_height + 1 + tui._cli_prompt_line
        self.assertTrue(tui.stream.getvalue().endswith(f"\x1b[{expected_row};13H"))

    def test_prompt_stays_at_the_bottom_and_allows_cursor_editing(self):
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.dimensions = lambda: (80, 20)
        tui.command = "ac"
        tui.command_cursor = 1
        tui.handle_key("b")
        self.assertEqual(tui.command, "abc")
        tui.handle_key("LEFT")
        tui.handle_key("DELETE")
        self.assertEqual(tui.command, "ac")
        tui.render()
        upper_height, lower_height = tui._panel_heights(20)
        self.assertEqual(tui._cli_prompt_line, lower_height - 1)
        self.assertIn(f"\x1b[{upper_height + lower_height};", tui.stream.getvalue())

    def test_renderer_overlays_frames_and_clears_only_after_resize(self):
        stream = io.StringIO()
        renderer = RichTuiRenderer(stream)

        renderer.render("uno", "", "", width=80, height=15, upper_height=8, lower_height=6)
        first_end = stream.tell()
        renderer.render("dos", "", "", width=80, height=15, upper_height=8, lower_height=6)
        second_end = stream.tell()
        renderer.render("tres", "", "", width=81, height=15, upper_height=8, lower_height=6)

        first = stream.getvalue()[:first_end]
        second = stream.getvalue()[first_end:second_end]
        resized = stream.getvalue()[second_end:]
        self.assertNotIn("\x1b[2J", first)
        self.assertNotIn("\x1b[2J", second)
        self.assertIn("\x1b[2J\x1b[H", resized)

    def test_dimensions_use_visible_terminal_viewport_and_fit_small_height(self):
        tui = LanwreTui(self.path, stream=io.StringIO())
        with (
            patch(
                "lanctl.apps.wire.tui.app.shutil.get_terminal_size",
                return_value=os.terminal_size((120, 30)),
            ),
            patch("lanctl.apps.wire.tui.app.terminal_columns", return_value=32),
            patch("lanctl.apps.wire.tui.app.terminal_rows", return_value=12),
        ):
            self.assertEqual(tui.dimensions(), (32, 12))
            self.assertEqual(sum(tui._panel_heights(12)) + 1, 12)
            tui.render()
        self.assertEqual(tui._last_size, (32, 12))
        self.assertNotIn("\x1b[2J", tui.stream.getvalue())

    def test_list_filters_by_idf_letters(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        result = CommandProcessor(database).execute("list sw")
        self.assertEqual(result.list_prefix, "SW")
        self.assertTrue(all(line.startswith("SW-") for line in result.lines))

    def test_show_without_id_uses_tui_selection(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        result = CommandProcessor(database).execute("show", selected_id="RT-02")
        self.assertEqual(result.view_id, "RT-02")

    def test_port_views_cover_router_switch_and_wire(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        records = database.all()
        by_id = {record["id"]: record for record in records}
        router = element_detail(by_id["RT-02"], records, 120).plain
        switch = element_detail(by_id["SW-02"], records, 120).plain
        wire = element_detail(by_id["WL-01"], records, 120).plain
        self.assertIn("[ RT-02.LAN1 ) --- <  WL-02  ]", router)
        self.assertIn("[ SW-02.24  ) --- <  WL-03  ]", switch)
        self.assertIn("SW-02.25  ]  [ SW-02.26", switch)
        self.assertIn("[ RT-01.LAN ) --- < WL-01 > --- ( RT-02.WLAN ]", wire)
        rt01_lines = element_detail(by_id["RT-01"], records, 120).plain.splitlines()
        self.assertEqual(rt01_lines[0].index(")"), rt01_lines[1].index(")"))

    def test_table_has_left_margin_and_enter_opens_modal(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        self.assertTrue(tui.tree_view(10, 100).plain.startswith("  IDF"))
        tui.selected_index = next(
            i for i, record in enumerate(tui.records) if record["id"] == "RT-02"
        )
        tui.handle_key("ENTER")
        self.assertEqual(tui.view_id, "RT-02")
        tui.dimensions = lambda: (120, 30)
        tui.render()
        self.assertIn("INFO", tui.stream.getvalue())
        tui.handle_key("ESC")
        self.assertIsNone(tui.view_id)
        tui.handle_key("F2")
        self.assertIsNone(tui.view_id)

    def test_global_shortcuts_open_local_lanwire_views_and_copy_selection(self):
        database = IDFDatabaseManager(self.path)
        database.add("SW-01", {"name": "Core"})
        tui = LanwreTui(self.path, stream=io.StringIO())

        tui.handle_key("F1")
        self.assertEqual(tui.utility_modal, "help")
        tui.handle_key("ESC")
        tui.handle_key("ENTER")
        self.assertEqual(tui.view_id, "SW-01")
        tui.handle_key("ESC")
        tui.handle_key("F7")
        self.assertEqual(tui.utility_modal, "plugins")
        tui.handle_key("ESC")
        tui.handle_key("F9")
        self.assertEqual(tui.utility_modal, "project")
        tui.handle_key("ESC")
        tui.handle_key("F12")
        self.assertEqual(tui.utility_modal, "settings")
        self.assertIn("EXCLUSIVA DE LANWIRE", tui._utility_modal_content()[1].plain)
        tui.handle_key("ESC")
        tui.handle_key("CTRL_C")
        self.assertEqual(tui.clipboard_text, "SW-01")
        tui.handle_key("CTRL_J")
        self.assertIn('"id": "SW-01"', tui.clipboard_text)

    def test_help_modal_has_lanip_style_sections_and_prepares_command(self):
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.dimensions = lambda: (120, 32)
        tui.handle_key("F1")
        title, body = tui._utility_modal_content()
        self.assertEqual(title, "HELP")
        self.assertIn("Comandos", body.plain)
        self.assertIn("idf list", body.plain)
        tui.handle_key("DOWN")
        tui.handle_key("DOWN")
        tui.handle_key("ENTER")
        self.assertIn("lanwire idf list", tui._utility_modal_content()[1].plain)
        tui.handle_key("RIGHT")
        self.assertIn("Ctrl+S", tui._utility_modal_content()[1].plain)
        tui.handle_key("TAB")
        self.assertIsNone(tui.utility_modal)
        self.assertEqual(tui.command, "idf list ")
        tui.handle_key("F1")
        tui.render()
        self.assertIn("HELP", tui.stream.getvalue())

    def test_local_settings_do_not_expose_network_configuration(self):
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.handle_key("F12")
        body = tui._utility_modal_content()[1].plain
        self.assertIn("Altura del panel CLI", body)
        self.assertNotIn("red", body.casefold())
        tui.handle_key("DOWN")
        tui.handle_key("DOWN")
        tui.handle_key("RIGHT")
        self.assertEqual(tui.settings_draft["tableDensity"], "compact")

    def test_malformed_numeric_settings_fall_back_to_defaults(self):
        from unittest.mock import patch

        from lanctl.apps.wire.tui.settings import load_settings

        with (
            patch("lanctl.apps.wire.tui.settings.settings_path", return_value=self.path),
            patch(
                "lanctl.apps.wire.tui.settings.read",
                return_value={"cliHeight": "broken", "columnWidths": {"idf": None}},
            ),
        ):
            settings = load_settings()
        self.assertEqual(settings["cliHeight"], 12)
        self.assertEqual(settings["columnWidths"]["idf"], 10)

    def test_local_settings_configure_columns_and_cli_layout(self):
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.handle_key("F12")
        for _ in range(6):
            tui.handle_key("DOWN")
        tui.handle_key("RIGHT")
        self.assertEqual(tui.settings_draft["columnWidths"]["idf"], 11)
        for _ in range(6):
            tui.handle_key("UP")
        tui.handle_key("RIGHT")
        self.assertEqual(tui.settings_draft["panelLayout"], "cli.top")

    def test_groups_filter_without_changing_the_idf(self):
        database = IDFDatabaseManager(self.path)
        database.add("BR-01", {"type": "wire"})
        database.add("RT-01", {"type": "device.router"})
        database.add("PC-01", {"type": "device.pc", "groups": ["LAB"]})
        processor = CommandProcessor(database)
        self.assertEqual([item["id"] for item in database.list_group("WIRE")], ["BR-01"])
        self.assertEqual([item["id"] for item in database.list_group("SWITCHS")], ["RT-01"])
        self.assertEqual(processor.execute("list @LAB").list_group, "LAB")
        self.assertEqual(database.get("PC-01")["id"], "PC-01")

    def test_graph_command_opens_a_physical_topology_view(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.command = "graph"
        tui.execute()
        self.assertEqual(tui.utility_modal, "graph")
        body = tui._utility_modal_content()[1].plain
        self.assertIn("TOPOLOGÍA FÍSICA", body)
        self.assertIn("WL-01", body)

    def test_modal_size_follows_visible_port_count(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        records = database.all()
        by_id = {record["id"]: record for record in records}
        two_ports = element_detail(by_id["RT-01"], records, 180)
        six_ports = element_detail(by_id["SW-03"], records, 180)
        self.assertEqual(RichTuiRenderer.modal_size(two_ports, "RT-01", 180, 50)[1], 6)
        self.assertEqual(RichTuiRenderer.modal_size(six_ports, "SW-03", 180, 50)[1], 10)
        self.assertEqual(len(six_ports.plain.splitlines()), 6)
        self.assertNotIn("][", six_ports.plain)
        self.assertLess(RichTuiRenderer.modal_size(two_ports, "RT-01", 180, 50)[0], 80)
        self.assertGreaterEqual(
            RichTuiRenderer.modal_size(two_ports, "RT-01", 180, 50)[0], modal_footer().cell_len + 4
        )

    def test_switch_layout_adapts_to_terminal_width_and_arbitrary_sizes(self):
        ports = {str(number): {"kind": "wire.copper"} for number in range(52)}
        record = {"id": "SW-99", "data": {"type": "device.switch", "ports": ports}}
        wide = element_detail(record, [record], 180).plain.splitlines()
        narrow = element_detail(record, [record], 40).plain.splitlines()
        self.assertEqual(len(wide), 26)
        self.assertEqual(len(narrow), 52)

    def test_sfp_dac_ports_are_marked_and_sidebar_is_composed(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        records = database.all()
        sw = next(record for record in records if record["id"] == "SW-02")
        detail = element_detail(sw, records, 140, selected_port="27")
        sidebar = element_sidebar(sw, records, selected_port="27")
        combined = combine_with_sidebar(detail, sidebar, 180).plain
        self.assertIn("SW-02.27*", combined)
        self.assertIn("connector: SFP/DAC", combined)
        self.assertIn("10G/1G/100M", combined)
        self.assertIn("│", combined)
        switch_rows = detail.plain.splitlines()
        self.assertEqual(switch_rows[-2].index("]"), switch_rows[-1].index("]"))
        selected = next(
            span for span in detail.spans if str(span.style) == "bold black on bright_cyan"
        )
        selected_text = detail.plain[selected.start : selected.end]
        self.assertTrue(selected_text.startswith("["))
        self.assertIn("SW-02.27*", selected_text)
        self.assertNotIn("SW-02.28*", selected_text)
        self.assertNotIn("\n", selected_text)
        right_detail = element_detail(sw, records, 140, selected_port="28")
        right_selected = next(
            span for span in right_detail.spans if str(span.style) == "bold black on bright_cyan"
        )
        right_text = right_detail.plain[right_selected.start : right_selected.end]
        self.assertIn("SW-02.28*", right_text)
        self.assertNotIn("SW-02.27*", right_text)

    def test_virtual_navigation_follows_cable_to_other_device(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RT-02"
        tui.modal_selection = 1  # LAN1 -> WL-02
        tui.handle_key("ENTER")
        for _ in range(4):
            tui.handle_key("DOWN")
        tui.handle_key("ENTER")
        self.assertEqual(tui.view_id, "WL-02")
        tui.handle_key("RIGHT")
        tui.handle_key("ENTER")
        self.assertEqual(tui.view_id, "SW-01")
        self.assertEqual(tui.modal_selection, 22)  # Puerto físico 23.
        tui.handle_key("BACKSPACE")
        self.assertEqual(tui.view_id, "WL-02")

    def test_f3_follows_a_physical_route_and_selects_the_opposite_endpoint(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "FB-01"
        tui.handle_key("RIGHT")  # El lado izquierdo del ejemplo es el suministro externo.
        tui.handle_key("F3")
        self.assertEqual((tui.view_id, tui.modal_selection), ("RT-01", 0))
        tui.handle_key("DOWN")
        tui.handle_key("F3")
        self.assertEqual((tui.view_id, tui.modal_endpoint), ("WL-01", 1))
        tui.handle_key("F3")
        self.assertEqual((tui.view_id, tui.modal_selection), ("RT-02", 0))
        tui.handle_key("DOWN")
        tui.handle_key("ENTER")
        self.assertEqual(tui.modal_focus, "menu")
        tui.handle_key("F3")
        self.assertEqual((tui.view_id, tui.modal_endpoint), ("WL-02", 1))
        tui.handle_key("F3")
        self.assertEqual((tui.view_id, tui.modal_selection), ("SW-01", 22))
        tui.handle_key("BACKSPACE")
        self.assertEqual((tui.view_id, tui.modal_endpoint), ("WL-02", 1))

    def test_wire_highlight_marks_only_selected_endpoint(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        records = database.all()
        wire = next(record for record in records if record["id"] == "WL-01")
        detail = element_detail(wire, records, 120, selected_endpoint=1)
        selected = next(
            span for span in detail.spans if str(span.style) == "bold black on bright_cyan"
        )
        self.assertEqual(detail.plain[selected.start : selected.end], "RT-02.WLAN")

    def test_empty_wire_side_is_selectable_connectable_and_disconnectable(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        wire = database.get("WL-03")
        data = wire["data"]
        data["endpoints"] = data["endpoints"][:1]
        database.update("WL-03", data)
        records = database.all()
        wire = next(record for record in records if record["id"] == "WL-03")
        detail = element_detail(wire, records, 120, selected_endpoint=1)
        selected = next(
            span for span in detail.spans if str(span.style) == "bold black on bright_cyan"
        )
        self.assertEqual(detail.plain[selected.start : selected.end], "?")

        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "WL-03"
        tui.modal_endpoint = 1
        tui.handle_key("TAB")
        tui.handle_key("TAB")
        tui.handle_key("ENTER")
        tui.action_buffer = "SW-02.1"
        tui.handle_key("ENTER")
        self.assertIn({"device": "SW-02", "port": "1"}, database.get("WL-03")["data"]["endpoints"])
        tui.handle_key("ENTER")
        self.assertNotIn(
            {"device": "SW-02", "port": "1"}, database.get("WL-03")["data"]["endpoints"]
        )

    def test_rack_units_are_scrollable_and_open_their_occupant(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        records = database.all()
        rack = next(record for record in records if record["id"] == "RK-00")
        self.assertEqual(len(selectable_ports(rack)), 18)
        detail = element_detail(rack, records, 100, selected_port="18")
        self.assertIn("U01", detail.plain)
        self.assertIn("U18", detail.plain)
        selected = next(
            span for span in detail.spans if str(span.style) == "bold black on bright_cyan"
        )
        self.assertIn("U18", detail.plain[selected.start : selected.end])
        pdu_row = next(line for line in detail.plain.splitlines() if line.startswith("U16"))
        self.assertEqual(pdu_row.count("O"), 8)
        tray_top = next(line for line in detail.plain.splitlines() if line.startswith("U03"))
        tray_bottom = next(line for line in detail.plain.splitlines() if line.startswith("U04"))
        self.assertIn("│", tray_top)
        self.assertNotIn("─", tray_top)
        self.assertIn("└", tray_bottom)
        self.assertIn("┘", tray_bottom)

        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RK-00"
        tui.modal_selection = 12  # U13 contiene SW-01.
        tui.handle_key("ENTER")
        self.assertEqual(tui.view_id, "SW-01")
        tui.handle_key("BACKSPACE")
        self.assertEqual((tui.view_id, tui.modal_selection), ("RK-00", 12))

    def test_tall_rack_view_scroll_follows_selected_unit(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RK-00"
        tui.modal_selection = 17
        tui.dimensions = lambda: (100, 16)
        tui.render()
        self.assertGreater(tui.modal_scroll, 0)
        self.assertIn("RK-00", tui.stream.getvalue())
        self.assertIn("R0", tui.stream.getvalue())

    def test_modal_keeps_its_largest_size_while_selection_moves(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-02"
        tui.dimensions = lambda: (140, 35)
        tui.render()
        initial = tui._modal_size_locked
        tui.modal_selection = 27
        tui.render()
        self.assertEqual(tui._modal_size_locked, initial)
        self.assertEqual(tui._modal_size_key, ("SW-02", 140, 35, "view"))

        tui.dimensions = lambda: (100, 25)
        tui.render()
        self.assertEqual(tui._modal_size_key, ("SW-02", 100, 25, "view"))

    def test_switch_view_does_not_reserve_hidden_editor_height(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "SW-00",
            {
                "type": "device.switch",
                "ports": {f"X{number}": {"kind": "wire.copper"} for number in range(1, 25)},
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-00"
        tui.dimensions = lambda: (140, 40)
        tui.render()
        view_height = tui._modal_size_locked[1]
        self.assertLess(view_height, 25)
        tui.modal_focus = "editor"
        tui.render()
        self.assertGreater(tui._modal_size_locked[1], view_height)
        tui.modal_focus = "view"
        tui.render()
        self.assertEqual(tui._modal_size_locked[1], view_height)

    def test_tab_editor_updates_selected_port_data(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RT-02"
        tui.modal_selection = 0
        tui.handle_key("TAB")
        tui.handle_key("DOWN")
        tui.handle_key("ENTER")
        self.assertEqual(tui.modal_focus, "editor")
        fields = tui._editing_fields(tui._modal_record())
        tui.editor_selection = next(
            index for index, field in enumerate(fields) if field.label == "WLAN.speeds"
        )
        tui.handle_key("ENTER")
        tui.editor_buffer = "5G/2.5G/1G"
        tui.handle_key("ENTER")
        speeds = database.get("RT-02")["data"]["ports"]["WLAN"]["speeds"]
        self.assertEqual(speeds, ["5G", "2.5G", "1G"])
        tui.handle_key("TAB")
        self.assertEqual(tui.modal_focus, "menu")
        tui.handle_key("TAB")
        self.assertEqual(tui.modal_focus, "view")

    def test_optional_ip_field_is_editable_and_validated(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RT-02"
        tui.handle_key("TAB")
        tui.handle_key("ENTER")
        fields = tui._editing_fields(tui._modal_record())
        tui.editor_selection = next(
            index for index, field in enumerate(fields) if field.label == "ip"
        )
        tui.handle_key("ENTER")
        tui.editor_buffer = "192.168.1.1"
        tui.handle_key("ENTER")
        self.assertEqual(database.get("RT-02")["data"]["ip"], "192.168.1.1")
        sidebar = element_sidebar(database.get("RT-02"), database.all(), selected_port="WLAN")
        self.assertIn("ip: 192.168.1.1", sidebar.plain)

    def test_editor_shows_and_applies_contextual_options_in_its_side_panel(self):
        database = IDFDatabaseManager(self.path)
        database.add("DV-01", {"type": "element", "name": "Nuevo"})
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "DV-01"
        tui.handle_key("TAB")
        tui.handle_key("RIGHT")
        self.assertEqual(tui.editor_option_index, 0)
        tui.dimensions = lambda: (120, 30)
        tui.render()
        self.assertIn("OPCIONES · type", tui.stream.getvalue())
        tui.handle_key("ENTER")
        self.assertEqual(database.get("DV-01")["data"]["type"], "device.router")

    def test_editor_can_resize_and_rename_device_ports(self):
        database = IDFDatabaseManager(self.path)
        database.add("DV-01", {"type": "device.pc", "ports": {"LAN1": {"kind": "wire.copper"}}})
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "DV-01"
        tui.handle_key("TAB")
        tui.handle_key("ENTER")
        fields = tui._editing_fields(tui._modal_record())
        tui.editor_selection = next(
            index for index, field in enumerate(fields) if field.label == "portCount"
        )
        tui.handle_key("RIGHT")
        tui.editor_option_index = 1  # 2 puertos
        tui.handle_key("ENTER")
        self.assertEqual(list(database.get("DV-01")["data"]["ports"]), ["LAN1", "LAN2"])
        self.assertIn("LAN2", tui._modal_record()["data"]["ports"])
        tui.dimensions = lambda: (120, 32)
        tui.render()
        self.assertIn("DV-01.LAN2", tui.stream.getvalue())
        tui.handle_key("ESC")
        self.assertEqual(tui.modal_focus, "menu")
        self.assertEqual(tui.view_id, "DV-01")

    def test_port_count_can_shrink_free_ports_but_not_connected_ports(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "DV-01",
            {
                "type": "device.pc",
                "portNaming": "LAN{n}",
                "ports": {
                    "LAN1": {"kind": "wire.copper", "poe": True},
                    "LAN2": {"kind": "wire.copper"},
                    "LAN3": {"kind": "wire.copper"},
                },
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "DV-01"
        tui.modal_focus = "editor"
        tui.editor_scope = "general"
        tui.editor_selection = next(
            i
            for i, field in enumerate(tui._editing_fields(tui._modal_record()))
            if field.label == "portCount"
        )
        tui.editor_buffer = "2"
        tui.handle_key("ENTER")
        self.assertEqual(list(database.get("DV-01")["data"]["ports"]), ["LAN1", "LAN2"])
        self.assertTrue(database.get("DV-01")["data"]["ports"]["LAN1"]["poe"])

        database.add(
            "WL-01",
            {
                "type": "wire",
                "kind": "wire.copper",
                "endpoints": [{"device": "DV-01", "port": "LAN2"}],
            },
        )
        tui.reload()
        tui.editor_buffer = "1"
        tui.handle_key("ENTER")
        self.assertEqual(len(database.get("DV-01")["data"]["ports"]), 2)
        self.assertTrue(any("desconecta antes" in message for message in tui.messages))

    def test_switch_resize_preserves_existing_ports_and_adds_missing_ids(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "SW-01",
            {
                "type": "device.switch",
                "portNaming": "X{n}",
                "ports": {
                    "X1": {"kind": "wire.copper", "poe": True},
                    "X3": {"kind": "wire.copper"},
                },
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-01"
        tui.modal_focus = "editor"
        tui.editor_scope = "general"
        tui.editor_selection = next(
            i
            for i, field in enumerate(tui._editing_fields(tui._modal_record()))
            if field.label == "portCount"
        )
        tui.editor_buffer = "3"
        tui.handle_key("ENTER")
        ports = database.get("SW-01")["data"]["ports"]
        self.assertEqual(list(ports), ["X1", "X3", "X2"])
        self.assertTrue(ports["X1"]["poe"])

    def test_editor_can_generate_multiple_port_series_and_rename_one_port(self):
        database = IDFDatabaseManager(self.path)
        database.add("SW-01", {"type": "device.switch", "ports": {"X1": {"kind": "wire.copper"}}})
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-01"
        tui.modal_focus = "editor"
        tui.editor_scope = "general"
        tui.editor_selection = next(
            i
            for i, field in enumerate(tui._editing_fields(tui._modal_record()))
            if field.label == "portNaming"
        )
        tui.editor_buffer = "X{n}:2,XG{a}:2,FIBER"
        tui.handle_key("ENTER")
        self.assertEqual(
            list(database.get("SW-01")["data"]["ports"]), ["X1", "X2", "XG1", "XG2", "FIBER"]
        )
        tui.editor_scope = "port"
        tui.modal_selection = 2
        tui.editor_selection = 0
        self.assertEqual(tui._editing_fields(tui._modal_record())[0].label, "XG1.name")
        tui.editor_buffer = "UPLINK"
        tui.handle_key("ENTER")
        self.assertIn("UPLINK", database.get("SW-01")["data"]["ports"])
        tui.editor_selection = 1
        tui.editor_buffer = "1"
        tui.handle_key("ENTER")
        self.assertEqual(next(iter(database.get("SW-01")["data"]["ports"])), "UPLINK")

    def test_multi_series_port_count_resizes_final_series(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "SW-01",
            {
                "type": "device.switch",
                "portNaming": "X{n}:2,XG{a}:2",
                "ports": {
                    "X1": {"kind": "wire.copper"},
                    "X2": {"kind": "wire.copper"},
                    "XG1": {"kind": "wire.copper"},
                    "XG2": {"kind": "wire.copper"},
                },
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-01"
        tui.modal_focus = "editor"
        tui.editor_scope = "general"
        tui.editor_selection = next(
            i
            for i, field in enumerate(tui._editing_fields(tui._modal_record()))
            if field.label == "portCount"
        )
        tui.editor_buffer = "5"
        tui.handle_key("ENTER")
        self.assertEqual(database.get("SW-01")["data"]["portNaming"], "X{n}:2,XG{a}:3")
        self.assertIn("XG3", database.get("SW-01")["data"]["ports"])

    def test_port_editor_can_delete_one_free_port_but_protects_connected_port(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "SW-01",
            {
                "type": "device.switch",
                "ports": {
                    "X1": {"kind": "wire.copper"},
                    "X2": {"kind": "wire.copper"},
                },
            },
        )
        database.add(
            "WL-01",
            {
                "type": "wire",
                "kind": "wire.copper",
                "endpoints": [{"device": "SW-01", "port": "X1"}],
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "SW-01"
        tui.modal_focus = "editor"
        tui.editor_scope = "port"
        tui.editor_selection = next(
            i
            for i, field in enumerate(tui._editing_fields(tui._modal_record()))
            if field.label == "Eliminar puerto"
        )
        tui.handle_key("ENTER")
        tui.handle_key("ENTER")
        self.assertIn("X1", database.get("SW-01")["data"]["ports"])
        self.assertTrue(any("Desconecta WL-01" in message for message in tui.messages))
        tui.modal_selection = 1
        tui.handle_key("ENTER")
        tui.handle_key("ENTER")
        self.assertEqual(list(database.get("SW-01")["data"]["ports"]), ["X1"])
        self.assertEqual(tui.modal_focus, "menu")

    def test_wire_connect_shows_compatible_free_port_selector(self):
        database = IDFDatabaseManager(self.path)
        database.add(
            "DV-01",
            {
                "type": "device.pc",
                "ports": {
                    "LAN1": {"kind": "wire.copper"},
                    "FIBER": {"kind": "wire.fiber"},
                },
            },
        )
        database.add("WL-01", {"type": "wire", "kind": "wire.copper", "endpoints": []})
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "WL-01"
        tui.modal_focus = "actions"
        tui.handle_key("ENTER")
        self.assertEqual(tui._action_options(), ("DV-01.LAN1",))
        self.assertEqual(tui.action_option_index, 0)
        tui.handle_key("ENTER")
        self.assertEqual(
            database.get("WL-01")["data"]["endpoints"], [{"device": "DV-01", "port": "LAN1"}]
        )

    def test_cable_selector_filters_idfs_without_showing_incompatible_or_full_wires(self):
        database = IDFDatabaseManager(self.path)
        database.add("DV-01", {"type": "device.pc", "ports": {"LAN1": {"kind": "wire.copper"}}})
        database.add("WL-01", {"type": "wire", "kind": "wire.copper", "endpoints": []})
        database.add("WL-02", {"type": "wire", "kind": "wire.copper", "endpoints": []})
        database.add("WL-03", {"type": "wire", "kind": "wire.fiber", "endpoints": []})
        database.add(
            "WL-04",
            {
                "type": "wire",
                "kind": "wire.copper",
                "source": "externo",
                "endpoints": [{"device": "DV-02", "port": "LAN1"}],
            },
        )
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "DV-01"
        tui.modal_focus = "actions"
        tui.handle_key("ENTER")
        self.assertEqual(tui._action_options(), ("WL-01", "WL-02"))
        tui.dimensions = lambda: (120, 32)
        tui.render()
        self.assertIn("CABLES COMPATIBLES", tui.stream.getvalue())
        tui.handle_key("0")
        tui.handle_key("2")
        self.assertEqual(tui._action_options(), ("WL-02",))
        self.assertEqual(tui.action_option_index, 0)
        tui.handle_key("X")
        self.assertEqual(tui._action_options(), ())
        tui.handle_key("ENTER")
        self.assertEqual(database.get("WL-02")["data"]["endpoints"], [])
        tui.handle_key("BACKSPACE")
        self.assertEqual(tui._action_options(), ("WL-02",))
        tui.handle_key("ENTER")
        self.assertEqual(
            database.get("WL-02")["data"]["endpoints"], [{"device": "DV-01", "port": "LAN1"}]
        )

    def test_fixed_kind_field_opens_selectable_values_on_enter(self):
        database = IDFDatabaseManager(self.path)
        database.add("WL-01", {"type": "wire", "kind": "wire.copper"})
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "WL-01"
        tui.modal_focus = "editor"
        tui.editor_selection = next(
            i
            for i, field in enumerate(tui._editing_fields(tui._modal_record()))
            if field.label == "kind"
        )
        tui.handle_key("ENTER")
        self.assertEqual(tui.editor_option_index, 0)
        self.assertEqual(tui._editor_options(tui._editor_field()), ("RJ45", "Fibra", "SFP/DAC"))
        tui.handle_key("DOWN")
        tui.handle_key("ENTER")
        self.assertEqual(database.get("WL-01")["data"]["kind"], "wire.fiber")

    def test_connection_browser_keeps_action_and_filtered_idfs_side_by_side(self):
        browser = connection_browser_view(("WL-01", "WL-02"), 1, "02")
        self.assertIn("ACTIONS", browser.plain)
        self.assertIn("CABLES COMPATIBLES · 2", browser.plain)
        self.assertIn("Buscar IDF: 02", browser.plain)
        self.assertIn("▶ WL-02", browser.plain)
        self.assertEqual(
            browser.plain.splitlines()[0].index("│"), browser.plain.splitlines()[1].index("│")
        )

    def test_structured_outlets_render_as_one_continuous_route(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        records = database.all()
        by_id = {record["id"]: record for record in records}
        outlet = element_detail(by_id["PX-01"], records, 180, selected_port="ROOM").plain
        self.assertIn("PN-01.01", outlet)
        self.assertIn("P1-X1", outlet)
        self.assertIn("PX-01.ROOM", outlet)
        self.assertEqual(len(outlet.splitlines()), 1)
        panel = element_detail(by_id["PN-01"], records, 180, selected_port="01").plain
        self.assertEqual(len(panel.splitlines()), 17)
        self.assertIn("P1-X17", panel)

    def test_connector_actions_disconnect_connect_and_move(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RT-02"
        tui.modal_selection = 1  # LAN1 enlazado con WL-02.
        before = database.get("WL-02")["data"]["endpoints"]
        tui.handle_key("DELETE")
        self.assertEqual(database.get("WL-02")["data"]["endpoints"], before)
        tui.handle_key("TAB")
        self.assertEqual(tui.modal_focus, "menu")
        for _ in range(5):
            tui.handle_key("DOWN")
        tui.handle_key("ENTER")  # Desconectar.
        endpoints = database.get("WL-02")["data"]["endpoints"]
        self.assertEqual(endpoints, [{"device": "SW-01", "port": "23"}])
        self.assertIn("Desconectado WL-02 de RT-02.LAN1", tui.messages)

        tui.handle_key("ENTER")  # Conectar abre el selector filtrado.
        self.assertEqual(tui.action_option_index, 0)
        tui.action_option_index = tui._available_cables_for_selected_port().index("WL-02")
        tui.handle_key("ENTER")
        self.assertEqual(len(database.get("WL-02")["data"]["endpoints"]), 2)

        # El menú permite mover el cable sin recorrer los otros editores.
        for _ in range(4):
            tui.handle_key("DOWN")
        tui.handle_key("ENTER")
        tui.action_buffer = "LAN4"
        tui.handle_key("ENTER")
        endpoints = database.get("WL-02")["data"]["endpoints"]
        self.assertIn({"device": "RT-02", "port": "LAN4"}, endpoints)
        self.assertEqual(tui.modal_selection, 4)


if __name__ == "__main__":
    unittest.main()
