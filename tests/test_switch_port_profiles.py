"""Switch creation controls describe real ports and enforce tray-only equipment."""

import os
from pathlib import Path

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace
from test_physical_placement_gui import open_page, save_form
from test_project_sync import projects

from lanctl.apps.wire.topology import FIBER, build_new_idf_data, switch_creation_profiles
from lanctl.core.physical_placement import direct_mount_allowed
from lanctl.core.projects.workspace import activate_project_workspace


@pytest.mark.parametrize("profile", switch_creation_profiles(), ids=lambda p: p["kind"])
def test_switch_profiles_have_real_unique_ports(profile):
    data = build_new_idf_data(profile["kind"])
    assert data["type"] == "device.switch"
    assert len(data["ports"]) == profile["rj45"] + profile["sfp"]
    assert sum(port["kind"] == FIBER for port in data["ports"].values()) == profile["sfp"]
    assert all(p["connectorGender"] == "female" for p in data["ports"].values())
    assert direct_mount_allowed(data) is profile["rackmount"]


@pytest.mark.parametrize(
    "kind", ["router.gateway", "router.otg", "switch.5ports", "switch.6ports", "switch.8ports"]
)
def test_tray_only_devices_reject_direct_mount_and_preserve_identity(workspace, kind):
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    device = wire.wire_create({"kind": kind, "prefix": "DV"})["id"]
    before = wire._service.database.path.read_bytes()
    context = rack.bootstrap()["organizationRevision"]
    result = rack.rack_element(
        context, "update", device, {"rack": cabinet, "unit": 2, "in_rack": True}
    )
    assert not result["ok"] and result["errorId"]
    assert wire._service.database.path.read_bytes() == before
    # A direct API creation must enforce the same policy atomically.
    result = rack.rack_element(
        context, "create", "", {"kind": kind, "prefix": "XX", "rack": cabinet, "unit": 2}
    )
    assert not result["ok"]
    assert wire._service.database.path.read_bytes() == before
    tray = wire.wire_create(
        {"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": 3, "heightU": 2}
    )["id"]
    original = wire._service.database.get(device)
    assert rack.rack_element(
        rack.bootstrap()["organizationRevision"], "update", device, {"tray": tray}
    )["ok"]
    housed = wire._service.database.get(device)
    assert housed["id"] == device and housed["data"]["ports"] == original["data"]["ports"]
    assert housed["data"]["location"]["tray"] == tray
    assert (
        next(r for r in rack.bootstrap()["elements"] if r["id"] == device)["directMount"] is False
    )


def test_switch_sfp_connections_and_reopen(workspace, tmp_path):
    first, _ = projects(workspace, tmp_path)
    wire = api("lanwire")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    switch = wire.wire_create(
        {"kind": "switch.24rj45.4sfp", "prefix": "SW", "rack": cabinet, "unit": 1}
    )["id"]
    cable = wire.wire_create(
        {"kind": "wire.fiber", "prefix": "FB", "endpoints": [{"device": switch, "port": "SFP1"}]}
    )
    assert cable["ok"], cable
    assert wire.save_project()["ok"]
    activate_project_workspace(first, root=tmp_path / "fresh", refresh=True)
    rows = {r["id"]: r for r in wire.bootstrap()["records"]}
    assert len(rows[switch]["data"]["ports"]) == 28
    assert rows[cable["id"]]["data"]["endpoints"] == [{"device": switch, "port": "SFP1"}]


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
@pytest.mark.parametrize("language", ["es", "en"])
def test_grouped_switch_selection_and_unit_restrictions(workspace, tmp_path, monkeypatch, language):
    from lanctl.core import config
    from lanctl.shared import i18n

    projects(workspace, tmp_path)
    manager = i18n.LanguageManager(tmp_path / "languages")
    manager.initialize()
    manager.install(Path(__file__).resolve().parents[1] / "bundled/languages/spanish.lang")
    monkeypatch.setattr(i18n, "_MANAGER", manager)
    cfg = config.load_config()
    cfg["language"] = language
    config.save_config(cfg)
    wire, rack = api("lanwire"), api("lanrack")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    small = wire.wire_create({"kind": "switch.6ports", "prefix": "SM"})["id"]
    router = wire.wire_create({"kind": "router.gateway", "prefix": "RT"})["id"]
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    with playwright() as runtime:
        browser = runtime.chromium.launch(
            headless=True, executable_path=os.environ.get("LANCTL_CHROMIUM_EXECUTABLE")
        )
        page = open_page(browser, rack)
        page.set_default_timeout(7000)
        failures = []
        page.on("pageerror", lambda error: failures.append(str(error)))
        page.locator(f'[data-rack-open="{cabinet}"]').click()
        page.locator('[data-rack-unit="1"]').click(button="right")
        page.locator(".rack-unit-context > button").first.click()
        assert page.locator('[name="kind"]').input_value() == "switch"
        assert page.locator('[name="mountLocation"]').input_value() == "inside"
        page.locator('[name="kind"]').select_option("server.2ports")
        assert page.locator('[name="connectionMode"]').is_hidden()
        assert page.locator('[name="mountUnit"]').input_value() == "1"
        page.locator('[name="serverHeight"]').select_option("2")
        assert page.locator('[name="mountRange"]').input_value() == "U1\u2013U2"
        minus = page.locator(".rack-position-controls button").last
        plus = page.locator(".rack-position-controls button").first
        assert minus.is_disabled()
        plus.click()
        assert page.locator('[name="mountRange"]').input_value() == "U2\u2013U3"
        minus.click()
        page.locator('[name="mountUnit"]').evaluate(
            "e => {e.value=11; e.dispatchEvent(new Event('input'))}"
        )
        assert plus.is_disabled()
        assert page.locator('[name="mountRange"]').input_value() == "U11\u2013U12"
        page.locator('[name="mountLocation"]').select_option("environment")
        assert page.locator('[name="mountUnit"]').is_hidden()
        page.locator('[name="mountLocation"]').select_option("inside")
        page.locator('[name="mountUnit"]').evaluate(
            "e => {e.value=1; e.dispatchEvent(new Event('input'))}"
        )
        page.locator('[name="kind"]').select_option("switch")
        assert page.locator('[name="mountRange"]').input_value() == "U1"
        plus.click()
        assert page.locator('[name="mountRange"]').input_value() == "U2"
        for forbidden in ("router.gateway", "router.otg", "switch.5ports", "switch.6ports"):
            assert page.locator(f'[name="kind"] option[value="{forbidden}"]').count() == 0
        assert set(
            page.locator('[name="rj45Count"] option').evaluate_all(
                "options => options.map(o => o.value)"
            )
        ) == {"0", "16", "24", "48"}
        page.locator('[name="rj45Count"]').select_option("24")
        page.locator('[name="sfpCount"]').select_option("4")
        left = page.locator('[name="rj45Count"]').bounding_box()
        right = page.locator('[name="sfpCount"]').bounding_box()
        assert abs(left["y"] - right["y"]) < 2 and left["x"] + left["width"] < right["x"]
        # The pair remains side by side without overflowing a narrow viewport.
        page.set_viewport_size({"width": 780, "height": 700})
        narrow_left = page.locator('[name="rj45Count"]').bounding_box()
        narrow_right = page.locator('[name="sfpCount"]').bounding_box()
        assert abs(narrow_left["y"] - narrow_right["y"]) < 2
        assert narrow_right["x"] + narrow_right["width"] <= 780
        page.set_viewport_size({"width": 1440, "height": 1000})
        page.locator('[name="name"]').fill("24 RJ45 + 4 SFP")
        page.screenshot(path=str(tmp_path / f"switch-profile-{language}.png"))
        save_form(page)
        created = next(
            r for r in wire.bootstrap()["records"] if r["data"].get("name") == "24 RJ45 + 4 SFP"
        )
        assert len(created["data"]["ports"]) == 28
        assert "connectionMode" not in created["data"]
        assert created["data"]["location"]["in_rack"] is True
        assert created["data"]["location"]["unit"] == 2
        page.locator('[data-rack-unit="3"]').click(button="right")
        page.locator(".rack-unit-context > button").nth(1).click()
        for identifier in (small, router):
            assert page.locator(f'[name="element"] option[value="{identifier}"]').count() == 0
        # The independent creation form still offers desktop equipment for trays.
        page.locator("#cancel").click()
        page.evaluate("wireNew()")
        assert set(
            page.locator('[name="rj45Count"] option').evaluate_all(
                "options => options.map(o => o.value)"
            )
        ) == {"0", "5", "8", "16", "24", "48"}
        for copper in (5, 8, 16, 24, 48):
            page.locator('[name="rj45Count"]').select_option(str(copper))
            assert set(
                page.locator('[name="sfpCount"] option').evaluate_all(
                    "options => options.map(o => o.value)"
                )
            ) == {"0", "2", "4", "6"}
        page.locator('[name="rj45Count"]').select_option("0")
        assert set(
            page.locator('[name="sfpCount"] option').evaluate_all(
                "options => options.map(o => o.value)"
            )
        ) == {"4", "8", "12", "16", "24", "48"}
        page.locator('[name="sfpCount"]').select_option("48")
        page.locator('[name="name"]').fill("Optical 48")
        save_form(page)
        optical = next(
            r for r in wire.bootstrap()["records"] if r["data"].get("name") == "Optical 48"
        )
        assert len(optical["data"]["ports"]) == 48
        assert all(p["kind"] == FIBER for p in optical["data"]["ports"].values())
        assert rack.rack_element(
            rack.bootstrap()["organizationRevision"],
            "update",
            optical["id"],
            {"rack": cabinet, "unit": 3},
        )["ok"]
        page.evaluate("refresh()")
        assert (
            page.locator(f'[data-rack-occupant="{optical["id"]}"] [data-connector="sfp"]').count()
            == 48
        )
        page.evaluate(
            "([rack]) => wireNew('server.2ports', {rack, unit:6, in_rack:true, tray:null})",
            [cabinet],
        )
        assert page.locator('[name="serverPorts"] option').all_text_contents() == [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
        ]
        assert page.locator('[name="serverHeight"] option').all_text_contents() == [
            "1",
            "2",
            "3",
            "4",
        ]
        page.locator('[name="serverPorts"]').select_option("6")
        page.locator('[name="serverHeight"]').select_option("4")
        page.locator(".rack-size-position").scroll_into_view_if_needed()
        height_box = page.locator('[name="serverHeight"]').bounding_box()
        range_box = page.locator('[name="mountRange"]').bounding_box()
        assert abs(height_box["y"] - range_box["y"]) < 2
        page.screenshot(path=str(tmp_path / f"rack-size-position-{language}.png"))
        assert page.locator('[name="mountRange"]').input_value() == "U6\u2013U9"
        page.locator('[name="name"]').fill("Six-port server")
        save_form(page)
        server = next(
            r for r in wire.bootstrap()["records"] if r["data"].get("name") == "Six-port server"
        )
        assert len(server["data"]["ports"]) == 6
        assert server["data"]["rackAppearance"]["units"] == 4
        assert server["data"]["location"]["unit"] == 6
        page.evaluate("wireNew()")
        for kind in (
            "panel",
            "tray",
            "server.2ports",
            "blank",
            "ventilation",
            "organizer",
            "cable-comb",
            "pdu",
            "ups",
        ):
            page.locator('[name="kind"]').select_option(kind)
            assert page.locator(".switch-port-counts").is_hidden()
            assert page.locator('[name="heightU"]').is_visible() == (
                kind not in {"panel", "server.2ports"}
            )
            assert page.locator('[name="connectionMode"]').is_visible() == (kind == "server.2ports")
        page.locator('[name="kind"]').select_option("router.otg")
        assert page.locator(".switch-port-counts").is_hidden()
        assert not failures, failures
        browser.close()


def test_visual_rackmount_flag_cannot_override_desktop_identity():
    for kind in (
        "router.gateway",
        "router.otg",
        "switch.5ports",
        "switch.6ports",
        "switch.5rj45.6sfp",
        "switch.8rj45.4sfp",
        "switch.4sfp",
    ):
        data = build_new_idf_data(kind)
        data["rackAppearance"] = {
            "schemaVersion": 1,
            "kind": "switch",
            "rj45": 24,
            "sfp": 0,
            "units": 1,
            "rackmount": True,
        }
        assert not direct_mount_allowed(data)


def test_selection_matrix_exact_and_legacy_profiles_retained():
    profiles = switch_creation_profiles()
    assert {(p["rj45"], p["sfp"]) for p in profiles} == (
        {(c, 0) for c in (5, 8, 16, 24, 48)}
        | {(c, f) for c in (5, 8, 16, 24, 48) for f in (2, 4, 6)}
        | {(0, f) for f in (4, 8, 12, 16, 24, 48)}
        | {(26, 2)}
    )
    assert len(profiles) == 27
    for kind, expected in (
        ("switch.6ports", 6),
        ("switch.12ports", 12),
        ("switch.48rj45.8sfp", 56),
    ):
        assert len(build_new_idf_data(kind)["ports"]) == expected


@pytest.mark.parametrize(
    "kind",
    ["blank", "ventilation", "organizer", "cable-comb", "pdu", "ups", "tray", "server.2ports"],
)
def test_variable_height_rack_equipment(workspace, tmp_path, kind):
    projects(workspace, tmp_path)
    wire = api("lanwire")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    result = wire.wire_create(
        {"kind": kind, "prefix": "EQ", "rack": cabinet, "in_rack": True, "unit": 1, "heightU": 3}
    )
    assert result.get("ok"), result
    record = next(r for r in api("lanrack").bootstrap()["elements"] if r["id"] == result["id"])
    assert record["data"]["rackAppearance"]["units"] == 3
    if kind not in {"server.2ports", "tray"}:
        assert record["data"]["type"] == f"rack.{kind}"
        assert record["data"]["ports"] == {}
    overlap = wire.wire_create(
        {"kind": "panel", "prefix": "PN", "rack": cabinet, "in_rack": True, "unit": 2}
    )
    assert not overlap.get("ok")


@pytest.mark.parametrize("count", range(1, 7))
def test_server_port_counts(count):
    data = build_new_idf_data(f"server.{count}ports")
    assert data["type"] == "device.server"
    assert set(data["ports"]) == {f"LAN{n}" for n in range(1, count + 1)}


def test_tray_height_rejects_oversized_device_and_shrink(workspace):
    wire = api("lanwire")
    cabinet = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 12})["id"]
    tray = wire.wire_create(
        {"kind": "tray", "prefix": "TR", "rack": cabinet, "unit": 1, "heightU": 2}
    )["id"]
    before = wire._service.database.path.read_bytes()
    assert not wire.wire_create(
        {"kind": "router.gateway", "prefix": "RT", "tray": tray, "heightU": 3}
    )["ok"]
    assert wire._service.database.path.read_bytes() == before
    assert wire.wire_create({"kind": "router.gateway", "prefix": "RT", "tray": tray, "heightU": 2})[
        "ok"
    ]
    parent = wire._service.snapshot()["records"]
    parent = next(r for r in parent if r["id"] == tray)
    before = wire._service.database.path.read_bytes()
    assert not wire.wire_update(tray, parent["revision"], {"heightU": 1})["ok"]
    assert wire._service.database.path.read_bytes() == before
