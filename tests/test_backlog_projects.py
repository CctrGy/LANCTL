import zipfile
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from lanctl.apps.ip.interfaces.tui.main import LanctlTui
from lanctl.apps.ip.interfaces.tui.modal import ModalState, SettingField
from lanctl.core.projects.metadata import FIELDS, read_metadata, update_metadata
from lanctl.core.projects.vlf import create_project, inspect_project, update_project, verify_project


@pytest.fixture
def project(tmp_path, monkeypatch):
    from lanctl.core import config
    from lanctl.core.projects import catalog

    monkeypatch.setattr(config, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(catalog, "default_catalog_path", lambda: tmp_path / "projects.db")
    settings = {
        "database": str(tmp_path / "devices.json"),
        "groups": str(tmp_path / "groups.json"),
        "credentials": str(tmp_path / "credentials"),
        "range": "192.0.2.0/24",
    }
    path = tmp_path / "demo.vlf"
    create_project(path, config=settings, name="Original")
    return path, settings


def test_metadata_roundtrip_preserves_identity_inventory_and_future_save(project):
    from lanctl.core.projects.catalog import ProjectCatalog

    path, settings = project
    original = inspect_project(path)
    with zipfile.ZipFile(path) as archive:
        inventory = archive.read("devices/elements.db")
    data = read_metadata(path)
    values = {key: f"Valor {label}" for key, label, *_ in FIELDS}
    saved = update_metadata(path, values, data["revision"])
    assert saved["values"] == values
    assert saved["revision"] != data["revision"]
    assert inspect_project(path)["id"] == original["id"]
    assert ProjectCatalog().list(path.parent)[0].name == values["name"]
    verify_project(path)
    with zipfile.ZipFile(path) as archive:
        assert archive.read("devices/elements.db") == inventory
    update_project(path, config=settings)
    verify_project(path)
    assert read_metadata(path)["values"] == values
    values["description"] = ""
    update_metadata(path, values, read_metadata(path)["revision"])
    assert read_metadata(path)["values"]["description"] == ""


@pytest.mark.parametrize(
    "change",
    [{"name": " "}, {"author": 1}, {"company": "a" * 4097}, {"lan": "\x00"}, {"id": "replacement"}],
)
def test_invalid_metadata_never_changes_archive(project, change):
    path, _ = project
    snapshot = read_metadata(path)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        update_metadata(path, snapshot["values"] | change, snapshot["revision"])
    assert path.read_bytes() == before


def test_stale_metadata_edit_does_not_overwrite_other_window(project):
    path, _ = project
    snapshot = read_metadata(path)
    update_metadata(path, snapshot["values"] | {"name": "Otra ventana"}, snapshot["revision"])
    before = path.read_bytes()
    with pytest.raises(ValueError, match="otra ventana"):
        update_metadata(path, snapshot["values"] | {"author": "Stale"}, snapshot["revision"])
    assert path.read_bytes() == before


def test_metadata_disk_failure_preserves_original(project):
    path, _ = project
    snapshot = read_metadata(path)
    before = path.read_bytes()
    with (
        patch("lanctl.core.projects.vlf.os.replace", side_effect=OSError("disk full")),
        pytest.raises(OSError),
    ):
        update_metadata(path, snapshot["values"] | {"name": "New"}, snapshot["revision"])
    assert path.read_bytes() == before
    verify_project(path)


def test_tui_metadata_form_saves_and_requires_discard_confirmation(project):
    path, _ = project
    tui = LanctlTui.__new__(LanctlTui)
    tui._last_screen_lines = []
    tui.reload, tui.show_project_manager = Mock(), Mock()
    tui._edit_project_from_manager(path)
    assert len(tui.modal.items) == 7
    tui.modal.items[0].value = "Nueva oficina"
    tui.handle_key("ESC")
    tui.show_project_manager.assert_not_called()
    tui.handle_key("CTRL_S")
    assert read_metadata(path)["values"]["name"] == "Nueva oficina"
    tui.reload.assert_called_once()
    tui.show_project_manager.assert_called_once()
    tui._edit_project_from_manager(path)
    tui.modal.items[0].value = "Sin guardar"
    tui.handle_key("ESC")
    tui.handle_key("ESC")
    assert tui.show_project_manager.call_count == 2
    assert read_metadata(path)["values"]["name"] == "Nueva oficina"


@pytest.mark.parametrize("kind", ["projects", "plugins", "help", "events"])
@pytest.mark.parametrize("scanning", [True, False])
def test_remapped_save_in_modals_and_during_background_tasks(kind, scanning):
    tui = LanctlTui.__new__(LanctlTui)
    tui.modal = ModalState(kind, kind, ["Main"], [[]])
    tui.key_bindings = {"save": "F4"}
    tui.scanning = scanning
    tui.messages = []
    tui._manual_save, tui._update_manager_detail = Mock(), Mock()
    tui.handle_key("F4")
    tui._manual_save.assert_called_once()


@pytest.mark.parametrize("reason", ["no-active-project", "failed"])
def test_manual_save_missing_project_or_disk_failure_is_explicit(reason):
    tui = LanctlTui.__new__(LanctlTui)
    tui._set_terminal_message, tui.reload = Mock(), Mock()
    with (
        patch("lanctl.apps.ip.interfaces.tui.main.load_config", return_value={}),
        patch("lanctl.core.projects.save_policy.workspace_is_dirty", return_value=False),
        patch(
            "lanctl.core.projects.save_policy.save_active_project",
            side_effect=OSError("disk full") if reason == "failed" else None,
            return_value=SimpleNamespace(saved=False, reason=reason),
        ),
    ):
        tui._manual_save()
    assert (
        "No se pudo" if reason == "failed" else "No hay"
    ) in tui._set_terminal_message.call_args.args[0]
    tui.reload.assert_not_called()


def test_ctrl_s_saves_changed_settings_through_shared_service(monkeypatch):
    tui = LanctlTui.__new__(LanctlTui)
    field = SettingField("workers", "Workers", "--workers", "12", "8", "entero")
    tui.modal = ModalState("settings", "Settings", ["General"], [[]], items=[field])
    tui._capture = Mock(return_value=(0, "Guardado"))
    save = Mock()
    monkeypatch.setattr("lanctl.apps.suite.settings.save_form_values", save)
    tui.reload, tui._set_command_output = Mock(), Mock()
    tui.handle_key("CTRL_S")
    tui._capture.assert_not_called()
    assert save.call_args.args[0] == {"workers": "12"}
    assert tui.modal is None


def test_posix_ctrl_s_reaches_application_and_tty_restores_on_failure(monkeypatch):
    from lanctl.apps.ip.interfaces.tui.keyboard import posix_terminal_mode

    termios = SimpleNamespace(
        IXON=1, IXOFF=2, TCSADRAIN=1, tcgetattr=Mock(side_effect=[[7], [7]]), tcsetattr=Mock()
    )
    tty = SimpleNamespace(setcbreak=Mock())
    monkeypatch.setitem(__import__("sys").modules, "termios", termios)
    monkeypatch.setitem(__import__("sys").modules, "tty", tty)
    with pytest.raises(RuntimeError), posix_terminal_mode(SimpleNamespace(fileno=lambda: 5)):
        assert termios.tcsetattr.call_args.args[-1][0] == 4
        raise RuntimeError("render failed")
    assert termios.tcsetattr.call_args.args == (5, 1, [7])


def test_suite_metadata_api_keeps_validation_and_updates_catalog(project):
    from threading import RLock

    from lanctl.apps.suite.gui import SuiteApi

    path, _ = project
    api = SuiteApi.__new__(SuiteApi)
    api._lock = RLock()
    api._desktop = SimpleNamespace(_projects_payload=lambda: {"projects": []})
    data = api.project_metadata(str(path))
    assert data["ok"]
    values = data["values"] | {"author": "Equipo"}
    assert api.save_project_metadata(str(path), values, data["revision"])["ok"]
    assert not api.save_project_metadata(str(path), values, data["revision"])["ok"]
    assert read_metadata(path)["values"]["author"] == "Equipo"


@pytest.mark.parametrize("size", [(40, 12), (80, 24), (160, 50), (240, 70)])
def test_project_form_keeps_last_field_visible_after_resize(size):
    from rich.text import Text

    tui = LanctlTui.__new__(LanctlTui)
    fields = [
        SettingField(key, label, "", "Dato", "", "Texto", "PROJECT") for key, label, *_ in FIELDS
    ]
    tui.modal = ModalState("project_edit", "Editar", ["Datos"], [[]], items=fields, selected=6)
    tui.renderer = Mock()
    tui._render_modal(*size)
    body = tui.renderer.render_modal.call_args.kwargs["body"]
    assert any("Responsable" in row for row in body)
    assert all(Text.from_ansi(row).cell_len < size[0] for row in body)


def test_tui_output_and_command_history_have_bounded_retention():
    tui = LanctlTui.__new__(LanctlTui)
    tui._set_command_output("\n".join(f"message-{i}" for i in range(2500)), 0)
    assert len(tui.messages) == 2000
    assert tui.messages[0] == "message-500" and tui.messages[-1] == "message-2499"
    tui.command_history = [f"old-{i}" for i in range(500)]
    tui._clear_suggestions = Mock()
    tui.command = "version"
    tui.execute()
    assert len(tui.command_history) == 500
    assert tui.command_history[0] == "old-1" and tui.command_history[-1] == "version"


def test_keyboard_conflicts_reserved_keys_disable_and_restore_are_persisted(project):
    from lanctl.core.config import load_config
    from lanctl.core.settings_catalog import set_program_value

    for key in ("F1", "ENTER", "ESC", "CTRL_C"):
        with pytest.raises(ValueError):
            set_program_value("tui.keyBindings.save", key)
        assert load_config()["tuiKeyBindings"]["save"] == "CTRL_S"
    set_program_value("tui.keyBindings.save", None)
    assert load_config()["tuiKeyBindings"]["save"] is None
    set_program_value("tui.keyBindings.save", "CTRL_S")
    assert load_config()["tuiKeyBindings"]["save"] == "CTRL_S"


def test_metadata_edit_notifies_edited_project_instead_of_editors_active_project(project):
    from lanctl.core.config import load_config, save_config
    from lanctl.core.session import Session, bind_session

    path, settings = project
    save_config({**settings, "activeProject": str(path)})
    # An in-flight background job retains its originating project; interactive
    # windows now follow the shared selection instead of pinning independently.
    editor = Session("lanctl", "backend", {**load_config(), "activeProject": "other.vlf"})
    viewer = Session("lanip", "gui", load_config())
    for session in (editor, viewer):
        session.stop_event.set()
        session.thread.join()
    received = []
    viewer.handler = received.append
    try:
        with bind_session(editor):
            data = read_metadata(path)
            update_metadata(path, data["values"] | {"author": "New"}, data["revision"])
        viewer.poll()
        assert received == [{"action": "data-changed"}]
        assert editor.project == "other.vlf"
        assert viewer.project == str(path)
    finally:
        editor.close()
        viewer.close()
