"""Selected language reaches all launcher parsers without translating contracts/data."""

from pathlib import Path

import pytest

from lanctl.shared import i18n
from lanctl.shared.i18n import LanguageManager, language_context


@pytest.fixture
def languages(tmp_path, monkeypatch):
    manager = LanguageManager(tmp_path / "languages")
    manager.initialize("en")
    manager.install(Path(__file__).resolve().parents[1] / "bundled/languages/spanish.lang")
    monkeypatch.setattr(i18n, "_MANAGER", manager)
    return manager


@pytest.mark.parametrize("code", ["en", "es"])
def test_six_launcher_help_descriptions_and_technical_flags(languages, code):
    from lanctl.apps.access.manager_cli import build_parser as access
    from lanctl.apps.ip.interfaces.cli.main import build_parser as ip
    from lanctl.apps.rack.cli import build_parser as rack
    from lanctl.apps.wire.cli.main import build_parser as wire
    from lanctl.bootstrap.lanctl import build_parser as suite
    from lanctl.bootstrap.lanmon import build_parser as monitor

    with language_context(code):
        for build in (suite, ip, wire, rack, access, monitor):
            parser = build()
            help_text = parser.format_help()
            assert "LANCTL.UI." not in help_text
            assert ("Show the" if code == "en" else "Muestra la") in help_text
            assert "--version" in help_text and "--gui" in help_text
            assert "--cli" in help_text and "--tui" in help_text
    assert languages.selected == "en"


def test_wire_help_static_data_resolves_when_rendered(languages):
    from lanctl.apps.wire.tui.help import COMMANDS, help_view

    with language_context("en"):
        english = help_view(120, 30, 0, 0, 0).plain
    with language_context("es"):
        spanish = help_view(120, 30, 0, 0, 0).plain
    assert "Show this help." in english
    assert "Muestra esta ayuda." in spanish
    assert "LANCTL.UI." not in english + spanish
    assert all(entry.name in english for entry in COMMANDS)


def test_language_context_nests_and_does_not_change_settings(languages):
    key = "LANCTL.UI.TEXT.SAVE"
    with language_context("es"):
        assert i18n.t(key) == "Guardar"
        with language_context("en"):
            assert i18n.t(key) == "Save"
        assert i18n.t(key) == "Guardar"
        assert languages.presentation_payload()["code"] == "es"
    assert i18n.t(key) == "Save"


def test_direct_technical_log_preserves_original_content(languages, tmp_path):
    from lanctl.core.logger import write_log

    message = "Guardar user=Nombre ip=127.0.0.1 id=LANCTL.TEST.1 {raw}"
    with language_context("es"):
        path = write_log(message, directory=tmp_path / "logs")
    assert path.read_text().split(" ", 1)[1].strip() == message


def test_legacy_technical_keys_cannot_be_overridden_by_translations(languages):
    key = "LANCTL.PLUGIN.LOG.ACTION"
    languages.catalogs["es"].strings[key] = "changed {plugin_id} {action} {target} {result}"
    values = dict(plugin_id="plugin.original", action="run", target="127.0.0.1", result="ok")
    with language_context("es"):
        assert i18n.t(key, **values) == i18n.ENGLISH_STRINGS[key].format(**values)
        assert languages.presentation_payload()["strings"][key] == i18n.ENGLISH_STRINGS[key]


def test_localized_console_status_keeps_canonical_log(languages, capsys):
    from unittest.mock import patch

    from lanctl.core.console import status

    messages = []
    for code in ("en", "es"):
        with language_context(code), patch("lanctl.core.console.write_log", messages.append):
            status(i18n.t("LANCTL.COMMON.STATUS.PENDING"), i18n.t("LANCTL.UI.TEXT.SAVE"))
        assert ("Guardar" if code == "es" else "Save") in capsys.readouterr().err
    assert messages == ["[PENDING] Save", "[PENDING] Save"]


def test_translated_value_can_be_logged_directly_without_localizing_log(languages, tmp_path):
    from lanctl.core.logger import write_log

    with language_context("es"):
        text = i18n.t("LANCTL.UI.TEXT.SAVE")
        assert str(text) == "Guardar"
        path = write_log(text, directory=tmp_path / "logs")
    assert path.read_text().split(" ", 1)[1].strip() == "Save"


def test_translated_text_survives_deepcopy_and_pickle(languages):
    import copy
    import pickle

    with language_context("es"):
        value = i18n.t("LANCTL.UI.TEXT.SAVE")
    for restored in (copy.deepcopy(value), pickle.loads(pickle.dumps(value))):
        assert restored == "Guardar"
        assert restored.canonical_text == "Save"
        assert restored.source_text == "Guardar"


def test_navigation_tab_ids_do_not_depend_on_display_language(languages):
    from lanctl.apps.ip.interfaces.tui.modal import ModalState

    with language_context("en"):
        modal = ModalState("info", "Details", [i18n.t("LANCTL.UI.TEXT.PORTS")], [[]])
        assert modal.tabs == ["Puertos"]
        assert i18n.translate_label(modal.tabs[0]) == "Ports"
    with language_context("es"):
        assert i18n.translate_label(modal.tabs[0]) == "Puertos"


def test_plugin_specification_localizes_only_display_metadata(languages):
    source = {
        "title": "Recursos compartidos",
        "id": "Title.Shared",
        "columns": [{"field": "name", "label": "Nombre"}],
        "name": "Nombre",
        "requires": ["mac"],
    }
    with language_context("en"):
        result = i18n.translate_specification(source)
    assert result["title"] == "Shared resources"
    assert result["columns"][0] == {"field": "name", "label": "Name"}
    assert result["id"] == source["id"] and result["requires"] == ["mac"]
    assert result["name"] == source["name"]
    assert source["columns"][0]["label"] == "Nombre"


def test_catalog_import_is_lazy_but_dictionary_views_load_all_messages():
    import os
    import subprocess
    import sys

    code = """
import json
import sys
from lanctl.shared import i18n
assert 'lanctl.shared.ui_messages' not in sys.modules
assert not i18n._UI_READY
assert len(i18n.ENGLISH_STRINGS) > 2000
assert i18n._UI_READY
assert len(dict(i18n.ENGLISH_STRINGS)) == len(i18n.SPANISH_STRINGS)
assert json.loads(json.dumps(i18n.ENGLISH_STRINGS))['LANCTL.UI.TEXT.SAVE'] == 'Save'
"""
    result = subprocess.run(
        [sys.executable, "-c", code], env=os.environ.copy(), capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
