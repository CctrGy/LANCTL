import json
from unittest.mock import patch

import pytest

from lanctl.apps.suite.launcher_gui import LauncherApi
from lanctl.core import config
from lanctl.core.database import DeviceDatabase
from lanctl.core.session_context import ENVIRONMENT_KEY, child_environment, consume_context


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    root = tmp_path / "data"
    marker = root / "config/migration-v2.complete"
    marker.parent.mkdir(parents=True)
    marker.write_text("LANCTL-DATA-V2\n")
    monkeypatch.setenv("LANCTL_DATA_DIR", str(root))
    monkeypatch.setattr(config, "CONFIG_PATH", root / "config/config.json")
    cfg = config.load_config()
    cfg.update(
        database=str(root / "devices.json"),
        groups=str(root / "groups.json"),
        physicalDatabase=str(root / "idf.db"),
        credentials=str(root / "credentials.vault"),
        monitorDatabase=str(root / "monitor.db"),
        monitorLock=str(root / "monitor.lock"),
        activeProject=None,
        projectWorkspace=None,
    )
    config.save_config(cfg)
    return cfg


def api(launcher, **options):
    with patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"):
        return LauncherApi(launcher, **options)


def test_wire_real_connections_port_rename_and_stale_edits(workspace):
    wire = api("lanwire")
    assert wire.wire_create({"kind": "switch.5ports", "prefix": "SW", "name": "Distribución"})["ok"]
    assert wire.wire_create({"kind": "pc.1port", "prefix": "PC", "name": "Puesto"})["ok"]
    cable = wire.wire_create({"kind": "wire.copper", "prefix": "WL", "name": "Enlace"})["id"]
    rows = wire.bootstrap()["records"]
    switch = next(r for r in rows if r["prefix"] == "SW")
    pc = next(r for r in rows if r["prefix"] == "PC")

    def get():
        return next(r for r in wire.bootstrap()["records"] if r["id"] == cable)

    endpoints = [{"device": switch["id"], "port": "X1"}, {"device": pc["id"], "port": "LAN1"}]
    assert wire.wire_connect(cable, get()["revision"], endpoints)["ok"]
    assert wire.wire_port(switch["id"], switch["revision"], "X1", "DESPACHO", 1)["ok"]
    assert get()["data"]["endpoints"][0]["port"] == "DESPACHO"
    stale = get()["revision"]
    assert wire.wire_update(cable, stale, {"description": "Documentado"})["ok"]
    assert not wire.wire_update(cable, stale, {"name": "Conflicto"})["ok"]
    assert get()["data"]["name"] == "Enlace"
    assert api("lanwire").bootstrap()["records"] == wire.bootstrap()["records"]


def test_wire_rejects_incompatible_and_occupied_ports(workspace):
    wire = api("lanwire")
    device = wire.wire_create({"kind": "switch.5ports", "prefix": "SW"})["id"]
    copper = wire.wire_create({"kind": "wire.copper", "prefix": "WL"})["id"]
    fiber = wire.wire_create({"kind": "wire.fiber", "prefix": "FB"})["id"]

    def revision(identifier):
        return next(x for x in wire.bootstrap()["records"] if x["id"] == identifier)["revision"]

    endpoint = [{"device": device, "port": "X1"}]
    assert not wire.wire_connect(fiber, revision(fiber), endpoint)["ok"]
    assert wire.wire_connect(copper, revision(copper), endpoint)["ok"]
    other = wire.wire_create({"kind": "wire.copper", "prefix": "WL"})["id"]
    assert not wire.wire_connect(other, revision(other), endpoint)["ok"]


def test_rack_reads_real_wire_storage_and_has_no_write_access(workspace):
    wire = api("lanwire")
    rack = wire.wire_create({"kind": "rack", "prefix": "RK", "units": 24, "name": "Principal"})[
        "id"
    ]
    device = wire.wire_create({"kind": "switch.5ports", "prefix": "SW"})["id"]
    record = next(r for r in wire.bootstrap()["records"] if r["id"] == device)
    assert wire.wire_update(device, record["revision"], {"rack": rack, "unit": 18})["ok"]
    reader = api("lanrack")
    row = reader.bootstrap()["records"][0]
    assert row["units"] == 24 and row["occupants"][0]["unit"] == 18
    assert not reader.wire_delete(rack, "anything")["ok"]


def test_access_portable_unlock_persistence_binding_and_no_secret_payload(workspace):
    device = DeviceDatabase(workspace["database"]).upsert(
        [{"IP": "192.0.2.10", "MAC": "02:00:00:00:00:10"}]
    )[0]
    access = api("lanaccess", cipher="portable")
    assert access.bootstrap()["locked"]
    assert not access.access_unlock("short", "short")["ok"]
    assert access.access_unlock("Vault-test-12345", "Vault-test-12345")["ok"]
    saved = access.access_set(device.device_id, "ssh", "operator", "device-secret", "device-secret")
    assert saved["ok"]
    payload = access.bootstrap()
    assert "device-secret" not in json.dumps(payload)
    assert "Vault-test" not in json.dumps(payload)
    assert payload["records"][0]["username"] == "operator"
    assert DeviceDatabase(workspace["database"]).load()[0].credentials["ssh"] == saved["id"]
    access.access_lock()
    assert access.bootstrap()["locked"]
    assert not access.access_delete(saved["id"])["ok"]
    fresh = api("lanaccess", cipher="portable")
    assert not fresh.access_unlock("incorrect")["ok"]
    assert fresh.access_unlock("Vault-test-12345")["ok"]
    assert fresh.access_delete(saved["id"])["ok"]
    assert fresh.bootstrap()["records"] == []
    assert not DeviceDatabase(workspace["database"]).load()[0].credentials


def test_monitor_open_does_not_probe_and_displays_persisted_samples(workspace):
    from lanctl.apps.monitor.database import MetricsStore, MonitorDatabase
    from lanctl.apps.monitor.models import CheckResult

    device = DeviceDatabase(workspace["database"]).upsert(
        [{"IP": "192.0.2.10", "MAC": "02:00:00:00:00:10"}]
    )[0]
    with MonitorDatabase(workspace["monitorDatabase"]) as db:
        MetricsStore(db).write(
            CheckResult("ping", device.device_id, True, latencyMs=4.2), "test-session"
        )
    with patch("lanctl.apps.monitor.commands._spawn_foreground") as spawn:
        monitor = api("lanmon")
        payload = monitor.bootstrap()
        spawn.assert_not_called()
    assert payload["ok"] and payload["records"][0]["latency"] == 4.2
    assert monitor.monitor_samples(device.device_id)["samples"][0]["latency_ms"] == 4.2
    assert not monitor.monitor_action("start")["ok"]  # No project selected.
    assert not monitor.monitor_action("shell")["ok"]


def test_child_session_context_is_one_shot_and_ignores_secret_paths(workspace, monkeypatch):
    env = child_environment("lanwire", {**workspace, "password": "never-export"}, {})
    assert "never-export" not in env[ENVIRONMENT_KEY]
    monkeypatch.setenv(ENVIRONMENT_KEY, env[ENVIRONMENT_KEY])
    assert consume_context("lanctl", {}) == {}
    assert consume_context("lanwire", {})["database"] == workspace["database"]
    assert consume_context("lanwire", {}) == {}


@pytest.mark.parametrize(
    "launcher,module",
    [
        ("lanwire", "lanctl.apps.wire.cli.main"),
        ("lanrack", "lanctl.apps.rack.cli"),
        ("lanaccess", "lanctl.apps.access.manager_cli"),
        ("lanmon", "lanctl.bootstrap.lanmon"),
    ],
)
def test_direct_and_routed_gui_entrypoints(launcher, module, workspace):
    import importlib

    from lanctl.bootstrap.lanctl import main

    entry = importlib.import_module(module)
    with patch("lanctl.apps.suite.launcher_gui.run_gui", return_value=0) as run:
        assert entry.main(["--gui"]) == 0
        assert main([launcher, "--gui"]) == 0
    assert run.call_count == 2


def test_fresh_layout_initializes_a_valid_plugin_registry(workspace):
    from lanctl.core.data_migration import ensure_data_layout
    from lanctl.core.paths import application_path
    from lanctl.core.plugins.manager import PluginManager

    ensure_data_layout()
    path = application_path(workspace["pluginRegistry"])
    assert json.loads(path.read_text()) == {"schemaVersion": 1, "plugins": {}}
    manager = PluginManager(path.parent, path)
    assert manager.list()


def test_wire_visual_metadata_validation_and_connections(workspace):
    wire = api("lanwire")
    device = wire.wire_create({"kind": "switch.5ports", "prefix": "SW"})["id"]
    cable = wire.wire_create({"kind": "wire.copper", "prefix": "WL"})["id"]

    def row(identifier):
        return next(r for r in wire.bootstrap()["records"] if r["id"] == identifier)

    assert wire.wire_connect(cable, row(cable)["revision"], [{"device": device, "port": "X1"}])[
        "ok"
    ]
    assert wire.wire_update(
        device,
        row(device)["revision"],
        {
            "connectionMode": "mixed",
            "groups": ["Oficina"],
            "ip": "192.0.2.12",
            "portChanges": {"X1": {"kind": "wire.copper", "poe": True}},
        },
    )["ok"]
    saved = row(device)
    assert saved["data"]["ports"]["X1"]["poe"]
    assert "OFICINA" in saved["filterGroups"]
    assert not wire.wire_update(device, saved["revision"], {"ip": "incorrecta"})["ok"]
    assert not wire.wire_update(device, saved["revision"], {"connectionMode": "unknown"})["ok"]
    assert not wire.wire_update(
        device,
        saved["revision"],
        {
            "portChanges": {"X1": {"kind": "wire.fiber", "poe": False}},
        },
    )["ok"]
    assert row(device) == saved


def test_wire_project_switch_and_failure_preserve_storage(workspace, tmp_path):
    from lanctl.core.projects.vlf import create_project

    cfg = config.load_config()
    cfg["projectsDirectory"] = str(tmp_path)
    config.save_config(cfg)
    path = tmp_path / "Office.vlf"
    create_project(path, name="Office", config=cfg, initialize_reserved=False)
    wire = api("lanwire")
    wire.wire_create({"kind": "switch.5ports", "prefix": "SW"})
    legacy_path = wire._service.database.path
    legacy_bytes = legacy_path.read_bytes()
    assert wire.use_project(str(path))["ok"]
    assert wire.bootstrap()["records"] == []
    assert legacy_path.read_bytes() == legacy_bytes
    assert wire.wire_create({"kind": "switch.5ports", "prefix": "SW"})["ok"]
    before = wire.bootstrap()
    assert before["project"] == str(path)
    assert len(before["records"]) == 1
    assert any(p["path"] == str(path) for p in wire.projects()["projects"])
    assert not wire.use_project(str(tmp_path / "missing.vlf"))["ok"]
    assert wire.bootstrap() == before


@pytest.mark.skipif(
    __import__("os").environ.get("LANCTL_GUI_BROWSER_TESTS") != "1",
    reason="optional browser runtime",
)
def test_wire_browser_real_service_interactions(workspace, tmp_path):
    from pathlib import Path

    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    from lanctl.core.projects.vlf import create_project

    cfg = config.load_config()
    cfg["projectsDirectory"] = str(tmp_path)
    config.save_config(cfg)
    project_path = tmp_path / "Visual.vlf"
    create_project(project_path, name="Visual", config=cfg, initialize_reserved=False)
    wire = api("lanwire")
    assert wire.use_project(str(project_path))["ok"]
    ids = [
        wire.wire_create({"kind": kind, "prefix": prefix, "name": name})["id"]
        for kind, prefix, name in [
            ("switch.5ports", "SW", "Switch central"),
            ("pc.1port", "PC", "Puesto"),
            ("wire.copper", "WL", "Enlace"),
            ("pc.1port", "PC", "Equipo Wi-Fi"),
        ]
    ]

    def row(identifier):
        return next(r for r in wire.bootstrap()["records"] if r["id"] == identifier)

    assert wire.wire_connect(
        ids[2],
        row(ids[2])["revision"],
        [{"device": ids[0], "port": "X1"}, {"device": ids[1], "port": "LAN1"}],
    )["ok"]
    assert wire.wire_update(ids[3], row(ids[3])["revision"], {"connectionMode": "wifi"})["ok"]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1100, "height": 780})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.expose_function("rpc", lambda method, args: getattr(wire, method)(*args))
        page.goto((Path(__file__).resolve().parents[1] / "gui/launcher.html").as_uri())
        page.evaluate(
            "window.pywebview={api:new Proxy({}, {get:(_,method)=>(...args)=>rpc(method,args)})};window.dispatchEvent(new Event('pywebviewready'))"
        )
        page.locator("#wire-board").wait_for()
        assert page.locator(".wire-node").count() == 2
        assert page.locator("#wire-lines path").count() == 1
        page.locator("#filter").select_option("wire")
        assert page.locator(".wire-node").count() == 2
        page.locator("#search").fill("Enlace")
        assert page.locator(".wire-node").count() == 2
        page.locator("#search").fill("")
        page.locator("#filter").select_option("")
        assert page.locator(".split").count() == 0
        page.locator('[data-nav="fit"]').click()
        page.screenshot(path=str(Path("tmp/lanwire-connected.png").resolve()))
        zoom = page.locator("#wire-zoom").inner_text()
        page.locator('[data-nav="in"]').click()
        assert page.locator("#wire-zoom").inner_text() != zoom
        board = page.locator("#wire-board").bounding_box()
        page.mouse.move(board["x"] + 15, board["y"] + 15)
        before = page.evaluate("camera.x")
        page.mouse.down()
        page.mouse.move(board["x"] + 55, board["y"] + 35)
        page.mouse.up()
        assert page.evaluate("camera.x") != before
        page.locator('[data-nav="mini"]').click()
        assert page.locator("#wire-minimap").is_visible()
        page.locator('[data-view="list"]').click()
        assert page.locator("#wire-board").count() == 0
        assert page.locator("tbody tr").count() == 4
        assert "device.switch" not in page.locator("#filter").inner_text()
        page.locator(f'tr[data-id="{ids[0]}"]').dblclick()
        assert page.locator(".wire-tabs button").count() == 6
        page.locator('[name="name"]').fill("Switch editado")
        page.get_by_role("tab", name="Datos técnicos", exact=True).click()
        page.locator('[name="groups"]').fill("Oficina, Red")
        page.get_by_role("tab", name="Puertos", exact=True).click()
        page.locator('[name="port_poe_X1"]').select_option("true")
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        assert row(ids[0])["data"]["name"] == "Switch editado"
        assert row(ids[0])["data"]["ports"]["X1"]["poe"]
        page.locator("#wire-filters").click()
        page.locator('[name="group"]').select_option("OFICINA")
        page.locator("#submit").click()
        page.wait_for_function("document.querySelectorAll('tbody tr').length===1")
        page.locator("tbody tr").dblclick()
        page.get_by_role("tab", name="JSON", exact=True).click()
        assert "Switch editado" in page.locator('[aria-label="Registro JSON"]').input_value()
        page.get_by_role("button", name="Centrar en Topología", exact=True).click()
        page.locator("#wire-board").wait_for()
        page.locator('[data-nav="focus"]').click()
        assert page.locator(".wire-node").count() == 1
        page.locator("#settings").click()
        page.get_by_role("tab", name="Topología", exact=True).click()
        page.locator('[name="pref_depth"]').fill("2")
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        assert page.evaluate("wirePrefs.depth") == 2
        page.get_by_role("button", name="Limpiar", exact=True).click()
        page.locator('[data-nav="all"]').click()
        page.locator('[data-nav="fit"]').click()
        page.locator(f'[data-node="{ids[0]}"] strong').dblclick()
        assert page.locator("#detail").is_visible()
        page.get_by_role("tab", name="JSON", exact=True).click()
        page.get_by_role("button", name="Copiar JSON", exact=True).click()
        page.locator("#cancel").click()
        page.locator('[data-view="list"]').click()
        page.locator(f'tr[data-id="{ids[0]}"]').click()
        page.wait_for_timeout(300)
        page.get_by_role("button", name="Editar puertos", exact=True).click()
        page.locator('[name="name"]').fill("OFICINA")
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        assert row(ids[2])["data"]["endpoints"][0]["port"] == "OFICINA"
        page.locator(f'tr[data-id="{ids[2]}"]').dblclick()
        page.get_by_role("tab", name="Conexiones", exact=True).click()
        page.get_by_role("button", name="Editar conexión", exact=True).click()
        page.locator('[name="b"]').select_option("")
        page.locator("#submit").click()
        page.wait_for_function("!document.querySelector('#detail').open")
        assert len(row(ids[2])["data"]["endpoints"]) == 1
        page.locator('[data-view="map"]').click()
        page.locator('[data-nav="all"]').click()
        page.locator('[data-nav="fit"]').click()
        page.screenshot(path=str(Path("tmp/lanwire-topology-full.png").resolve()))
        from lanctl.apps.suite.gui import SuiteApi

        assert page.locator("#wire-project").count() == 0
        assert not SuiteApi().use_project(str(project_path))["ok"]
        assert wire.save_project()["ok"]
        assert SuiteApi().use_project(str(project_path))["ok"]
        page.evaluate("window.launcherDataChanged=true")
        page.wait_for_function(
            "document.querySelector('footer #project-name').textContent==='Visual'"
        )
        assert wire.bootstrap()["project"] == str(project_path)
        assert row(ids[0])["data"]["name"] == "Switch editado"
        page.set_viewport_size({"width": 780, "height": 560})
        assert page.locator("footer").bounding_box()["y"] < 560
        assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
        page.screenshot(path=str(Path("tmp/lanwire-updated.png").resolve()))
        assert not errors, errors
        browser.close()


@pytest.mark.parametrize("kind,count", [("panel", 24), ("outlet", 2), ("router.gateway", 6)])
def test_wire_new_profiles_and_existing_connector_metadata(workspace, kind, count):
    wire = api("lanwire")
    result = wire.wire_create(
        {"kind": kind, "prefix": "ND", "name": "Infraestructura", "units": 42}
    )
    assert result["ok"], result
    row = next(r for r in wire.bootstrap()["records"] if r["id"] == result["id"])
    assert len(row["data"]["ports"]) == count
    changes = {
        name: {"kind": p["kind"], "poe": bool(p.get("poe"))}
        for name, p in row["data"]["ports"].items()
    }
    result = wire.wire_update(
        row["id"], row["revision"], {"description": "Actualizado", "portChanges": changes}
    )
    assert result["ok"], result
    saved = next(r for r in wire.bootstrap()["records"] if r["id"] == row["id"])
    assert saved["data"]["ports"] == row["data"]["ports"]
    assert "units" not in saved["data"]
