"""Regressions for a global selection with operation-local consistency."""

import json
import os
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import pytest
from test_launcher_gui import api
from test_launcher_gui import workspace as workspace

from lanctl.core import config
from lanctl.core.coordination import Coordinator
from lanctl.core.project_context import project_identity, project_operation
from lanctl.core.projects.workspace import activate_project_workspace
from lanctl.core.session import Session, bind_session


def projects(workspace, tmp_path):
    from lanctl.core.projects.vlf import create_project

    paths = []
    for name in ("First", "Second"):
        paths.append(
            create_project(
                tmp_path / (name + ".vlf"),
                name=name,
                config=workspace,
                initialize_reserved=False,
            )["path"]
        )
    activate_project_workspace(paths[0])
    return paths


def test_wire_switch_updates_all_six_live_adapters_and_rejects_old_forms(workspace, tmp_path):
    from lanctl.apps.ip.interfaces.gui.desktop import DesktopApi
    from lanctl.apps.suite.gui import SuiteApi

    first, second = projects(workspace, tmp_path)
    coordinator = Coordinator()
    with ExitStack() as stack:
        sessions, windows, snapshots = {}, {}, {}
        for launcher in ("lanctl", "lanip", "lanwire", "lanrack", "lanaccess", "lanmon"):
            session = Session(launcher, "gui", config.load_config(), coordinator=coordinator)
            stack.callback(session.close)
            session.stop_event.set()
            session.thread.join()
            sessions[launcher] = session
            with (
                bind_session(session),
                patch("lanctl.apps.ip.interfaces.gui.main.local_ipv4", return_value="127.0.0.1"),
            ):
                window = (
                    SuiteApi()
                    if launcher == "lanctl"
                    else DesktopApi()
                    if launcher == "lanip"
                    else api(launcher)
                )
                windows[launcher] = window
                snapshots[launcher] = window.bootstrap()
                assert snapshots[launcher]["ok"]
                assert snapshots[launcher]["projectContext"][0] == first
        old_access = windows["lanaccess"]._service
        old_access._unlocked = True
        old_access.manager.store._password = "test-only-secret"
        with bind_session(sessions["lanwire"]):
            result = windows["lanwire"].use_project(second)
            assert result["ok"], result
        # A stale view must not create anything in the new project, even if its
        # identifiers/revisions happen to be identical to the previous one.
        with bind_session(sessions["lanrack"]):
            rejected = windows["lanrack"].project_call(
                snapshots["lanrack"]["projectContext"], "rack_create", [{"name": "stale"}]
            )
            assert not rejected["ok"] and "proyecto cambió" in rejected["error"]
        for launcher, window in windows.items():
            received = []
            sessions[launcher].handler = received.append
            with bind_session(sessions[launcher]):
                sessions[launcher].poll()
                assert sessions[launcher].project == second
                payload = window.sync_project() if launcher == "lanip" else window.bootstrap()
                assert payload["ok"], payload
                assert payload["projectContext"][0] == second
                assert payload.get("activeProject", payload.get("project")) == second
        assert windows["lanrack"].bootstrap()["records"] == []
        assert old_access.manager.store._password is None
        assert not old_access._unlocked
        assert windows["lanaccess"]._service is not old_access


def test_running_operation_and_stale_settings_cannot_redirect_project(workspace, tmp_path):
    first, second = projects(workspace, tmp_path)
    original = config.load_config()
    # A second thread/process changes the persisted selection during a scan.
    with project_operation():
        assert config.load_config()["activeProject"] == first
        updated = deepcopy(original)
        updated.update(
            activeProject=second,
            database=str(tmp_path / "second.json"),
            range="198.51.100.0/24",
            workers=12,
        )
        config.CONFIG_PATH.write_text(
            json.dumps(config.canonical_config(updated)), encoding="utf-8"
        )
        assert config.load_config()["activeProject"] == first
        old = config.load_config()
        old["timeout"] = 2.0
        config.save_config(old)
        assert config.load_config()["activeProject"] == first
        assert config._load_config()["activeProject"] == second
        # Editing a storage preference is not a request to reselect the old
        # project. Preserve the newer selection even when one path changes.
        old = config.load_config()
        old["physicalDatabase"] = str(tmp_path / "changed-physical.db")
        config.save_config(old)
        assert config._load_config()["activeProject"] == second
        assert config._load_config()["physicalDatabase"] == str(tmp_path / "changed-physical.db")
    assert config.load_config()["activeProject"] == second
    assert config.load_config()["database"] == str(tmp_path / "second.json")
    assert config.load_config()["timeout"] == 2.0
    assert config.load_config()["range"] == "198.51.100.0/24"
    assert config.load_config()["workers"] == 12


def test_failed_and_dirty_project_switch_leave_every_session_unchanged(workspace, tmp_path):
    from lanctl.core.database import DeviceDatabase

    first, second = projects(workspace, tmp_path)
    wire = api("lanwire")
    assert not wire.use_project(str(tmp_path / "missing.vlf"))["ok"]
    DeviceDatabase(config.load_config()["database"]).upsert(
        [{"MAC": "02:00:00:00:00:01", "IP": "192.0.2.1"}]
    )
    rejected = wire.use_project(second)
    assert not rejected["ok"] and "pendientes" in rejected["error"]
    assert config.load_config()["activeProject"] == first
    assert len(DeviceDatabase(config.load_config()["database"]).load()) == 1


@pytest.mark.parametrize("method", ["__init__", "_respond", "project_call", "open_gui", "shell"])
def test_project_envelope_does_not_expose_arbitrary_methods(workspace, method):
    window = api("lanwire")
    result = window.project_call(project_identity(config.load_config()), method, [])
    assert not result["ok"]


def test_store_change_rebinds_rack_and_wire_and_rejects_previous_selection(workspace, tmp_path):
    from lanctl.apps.ip.interfaces.cli.main import build_parser

    rack, wire = api("lanrack"), api("lanwire")
    identifier = rack.rack_create({"prefix": "RK", "name": "Original", "units": 24})["id"]
    before = rack.bootstrap()
    original = rack._service
    args = build_parser().parse_args(
        ["settings", "--physical-database", str(tmp_path / "new-idf.db")]
    )
    assert args.handler(args) == 0
    rejected = rack.project_call(before["projectContext"], "rack_create", [{"name": "stale"}])
    assert not rejected["ok"]
    assert rack.bootstrap()["records"] == []
    assert wire.bootstrap()["records"] == []
    assert rack._service is not original
    assert original.snapshot()["records"][0]["id"] == identifier


def test_explicit_config_document_still_replaces_project_selection(workspace):
    document = config.canonical_config(config.load_config())
    document["projects"]["active"] = "chosen.vlf"
    config.save_config(config.config_from_document(document))
    assert config.load_config()["activeProject"] == "chosen.vlf"


def test_running_backend_keeps_its_project_when_selection_and_settings_change(workspace, tmp_path):
    first, second = projects(workspace, tmp_path)
    backend = Session("lanmon", "backend", config.load_config())
    backend.stop_event.set()
    backend.thread.join()
    try:
        activate_project_workspace(second)
        with bind_session(backend):
            backend.poll()
            assert config.load_config()["activeProject"] == first
            config.update_config(lambda c: c.update(monitorDatabase=str(tmp_path / "job.db")))
            assert backend.project == first
            assert config.load_config()["activeProject"] == first
        assert config.load_config()["activeProject"] == second
    finally:
        backend.close()


def test_switch_detects_competing_selection_before_commit(workspace, tmp_path):
    from lanctl.core.projects import workspace as workspace_module

    _, second = projects(workspace, tmp_path)
    prepare = workspace_module.prepare_project_workspace

    def competing(*args, **kwargs):
        prepared = prepare(*args, **kwargs)
        config.update_config(lambda c: c.update(activeProject="other.vlf"))
        return prepared

    with (
        patch.object(workspace_module, "prepare_project_workspace", side_effect=competing),
        pytest.raises(workspace_module.ProjectChangesPendingError, match="durante la apertura"),
    ):
        activate_project_workspace(second)
    assert config.load_config()["activeProject"] == "other.vlf"


def test_tui_reloads_and_preserves_a_stale_editor_until_cancelled(workspace, tmp_path):
    from lanctl.apps.ip.interfaces.tui.main import LanctlTui
    from lanctl.apps.ip.interfaces.tui.modal import ModalState

    _, second = projects(workspace, tmp_path)
    with patch("lanctl.apps.ip.interfaces.tui.main.local_ipv4", return_value="127.0.0.1"):
        tui = LanctlTui()
    original = tui.database.path
    tui.response_ms = {"same-device": 3.5}
    tui.active_devices = {"same-device"}
    tui.scan_summary = {"found": 1}
    tui.modal = ModalState(kind="info", title="Draft", tabs=["Details"], pages=[["Draft"]])
    activate_project_workspace(second)
    tui.handle_key("ENTER")
    assert tui.database.path == original
    assert tui.modal is not None and "proyecto cambió" in tui.modal.footer
    tui.handle_key("ESC")
    assert tui.modal is None
    assert tui.database.path != original
    assert tui._project_config["activeProject"] == second
    assert tui.response_ms == {}
    assert tui.active_devices == set()
    assert tui.scan_summary == {}


@pytest.mark.skipif(
    os.environ.get("LANCTL_GUI_BROWSER_TESTS") != "1", reason="optional browser runtime"
)
def test_browser_rejects_old_rack_form_and_refreshes_project_name(workspace, tmp_path):
    playwright = pytest.importorskip("playwright.sync_api").sync_playwright
    _, second = projects(workspace, tmp_path)
    rack, wire = api("lanrack"), api("lanwire")
    identifier = rack.rack_create({"prefix": "RK", "name": "Rack", "units": 24, "widthInches": 19})[
        "id"
    ]
    original_store = rack._service.database
    with playwright() as runtime:
        browser = runtime.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.expose_function("rpc", lambda method, args: getattr(rack, method)(*args))
        page.goto((Path(__file__).resolve().parents[1] / "gui/launcher.html").as_uri())
        page.evaluate(
            "window.pywebview={api:new Proxy({}, {get:(_,m)=>(...args)=>rpc(m,args)})};window.dispatchEvent(new Event('pywebviewready'))"
        )
        page.get_by_role("button", name="Editar dimensiones", exact=True).click()
        page.locator('[name="units"]').fill("42")
        assert not wire.use_project(second)["ok"]  # Physical changes are now pending changes.
        assert wire.save_project()["ok"]
        assert wire.use_project(second)["ok"]
        # Reuse the ID in the new project: revision/context, not the ID alone,
        # must prevent the previous form from editing this unrelated rack.
        assert (
            rack.rack_create({"prefix": "RK", "name": "Second rack", "units": 12})["id"]
            == identifier
        )
        page.locator("#submit").click()
        page.wait_for_function(
            "document.querySelector('#detail-error').textContent.includes('proyecto cambió')"
        )
        assert page.locator("#detail").evaluate("e=>e.open")
        assert page.locator('[name="units"]').input_value() == "42"
        assert next(r for r in rack.bootstrap()["records"] if r["id"] == identifier)["units"] == 12
        assert original_store.get(identifier)["data"]["units"] == 24
        page.evaluate("document.querySelector('#detail').close();refresh()")
        page.wait_for_function("document.querySelector('#project-name').textContent==='Second'")
        assert not errors
        browser.close()


@pytest.mark.parametrize("launcher", ["lanrack", "lanwire", "lanaccess"])
def test_real_gui_entrypoints_follow_project_storage_unless_explicit(workspace, tmp_path, launcher):
    from importlib import import_module

    module = import_module(
        {
            "lanrack": "lanctl.apps.rack.cli",
            "lanwire": "lanctl.apps.wire.cli.main",
            "lanaccess": "lanctl.apps.access.manager_cli",
        }[launcher]
    )
    entry = module._main if launcher == "lanaccess" else module.main
    with patch("lanctl.apps.suite.launcher_gui.run_gui", return_value=0) as launch:
        assert entry(["--gui"]) == 0
        assert launch.call_args.kwargs["database"] is None
        if launcher == "lanaccess":
            assert launch.call_args.kwargs["store"] is None
        explicit = str(tmp_path / "explicit.db")
        assert entry(["--gui", "--database", explicit]) == 0
        assert launch.call_args.kwargs["database"] == explicit
        if launcher == "lanaccess":
            vault = str(tmp_path / "explicit.vault")
            assert entry(["--gui", "--store", vault]) == 0
            assert launch.call_args.kwargs["store"] == vault
