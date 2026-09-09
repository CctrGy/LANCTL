import io
import tempfile
import unittest
from pathlib import Path

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
from lanctl.apps.wire.tui.editor import editable_fields
from lanctl.apps.wire.tui.keyboard import decode_windows_key
from lanctl.apps.wire.tui.renderer import RichTuiRenderer, modal_footer, separator_line


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
        self.assertEqual(processor.execute("add sw name=core").lines, ("Creado SW-00",))
        self.assertIn("SW-00", processor.execute("list").lines[0])

    def test_tui_builds_tree_and_cli_views(self):
        database = IDFDatabaseManager(self.path)
        database.add("AP-01", {"zone": "office"})
        tui = LanwreTui(self.path, stream=io.StringIO())
        self.assertIn("AP-01", tui.tree_view(10).plain)
        self.assertIn("lanwire>", tui.cli_view(8).plain)

    def test_windows_extended_key_is_decoded(self):
        keys = iter(("\xe0", "H"))
        self.assertEqual(decode_windows_key(lambda: next(keys)), "UP")

    def test_ascii_separator_has_no_vertical_borders(self):
        separator = separator_line("CLI", 40).plain
        self.assertEqual(separator, "-------[ CLI ]" + "-" * 26)
        self.assertNotIn("│", separator)

    def test_modal_footer_renders_padded_colored_keycaps(self):
        footer = modal_footer()
        self.assertEqual(footer.plain, " ↑/↓  desplazar    Tab  editar    F2  /  Esc  cerrar")
        self.assertEqual(footer.spans[0].style, "bold black on bright_cyan")

    def test_cursor_points_to_end_of_real_prompt(self):
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.command = "abc"
        tui.dimensions = lambda: (80, 20)
        tui.render()
        upper_height, _ = tui.panel_heights(20)
        expected_row = upper_height + 1 + tui._cli_prompt_line
        self.assertTrue(tui.stream.getvalue().endswith(f"\x1b[{expected_row};13H"))

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
        self.assertEqual(tui.view_id, "WL-02")
        tui.handle_key("RIGHT")
        tui.handle_key("ENTER")
        self.assertEqual(tui.view_id, "SW-01")
        self.assertEqual(tui.modal_selection, 22)  # Puerto físico 23.
        tui.handle_key("BACKSPACE")
        self.assertEqual(tui.view_id, "WL-02")

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
        self.assertEqual(tui._modal_size_key, ("SW-02", 140, 35))

        tui.dimensions = lambda: (100, 25)
        tui.render()
        self.assertEqual(tui._modal_size_key, ("SW-02", 100, 25))

    def test_tab_editor_updates_selected_port_data(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RT-02"
        tui.modal_selection = 0
        tui.handle_key("TAB")
        self.assertEqual(tui.modal_focus, "editor")
        fields = editable_fields(tui._modal_record(), "WLAN", 0)
        tui.editor_selection = next(
            index for index, field in enumerate(fields) if field.label == "WLAN.speeds"
        )
        tui.handle_key("ENTER")
        tui.editor_buffer = "5G/2.5G/1G"
        tui.handle_key("ENTER")
        speeds = database.get("RT-02")["data"]["ports"]["WLAN"]["speeds"]
        self.assertEqual(speeds, ["5G", "2.5G", "1G"])
        tui.handle_key("TAB")
        self.assertEqual(tui.modal_focus, "actions")
        tui.handle_key("TAB")
        self.assertEqual(tui.modal_focus, "view")

    def test_optional_ip_field_is_editable_and_validated(self):
        database = IDFDatabaseManager(self.path)
        seed_sample_topology(database)
        tui = LanwreTui(self.path, stream=io.StringIO())
        tui.view_id = "RT-02"
        tui.handle_key("TAB")
        fields = editable_fields(tui._modal_record(), "WLAN", 0)
        tui.editor_selection = next(
            index for index, field in enumerate(fields) if field.label == "ip"
        )
        tui.handle_key("ENTER")
        tui.editor_buffer = "192.168.1.1"
        tui.handle_key("ENTER")
        self.assertEqual(database.get("RT-02")["data"]["ip"], "192.168.1.1")
        sidebar = element_sidebar(database.get("RT-02"), database.all(), selected_port="WLAN")
        self.assertIn("ip: 192.168.1.1", sidebar.plain)

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
        tui.handle_key("TAB")
        self.assertEqual(tui.modal_focus, "actions")
        tui.handle_key("ENTER")  # Desconectar.
        endpoints = database.get("WL-02")["data"]["endpoints"]
        self.assertEqual(endpoints, [{"device": "SW-01", "port": "23"}])
        self.assertIn("Desconectado WL-02 de RT-02.LAN1", tui.messages)

        tui.handle_key("ENTER")  # Conectar pide el IDF.
        tui.action_buffer = "WL-02"
        tui.handle_key("ENTER")
        self.assertEqual(len(database.get("WL-02")["data"]["endpoints"]), 2)

        # Al estar conectado aparecen Desconectar y Mover.
        tui.action_selection = 1
        tui.handle_key("ENTER")
        tui.action_buffer = "LAN4"
        tui.handle_key("ENTER")
        endpoints = database.get("WL-02")["data"]["endpoints"]
        self.assertIn({"device": "RT-02", "port": "LAN4"}, endpoints)
        self.assertEqual(tui.modal_selection, 4)


if __name__ == "__main__":
    unittest.main()
