"""Versioned catalog regressions: migration, invalid documents and literal data."""

import json

import pytest

from lanctl.shared.i18n import ENGLISH_STRINGS, LanguageManager, _english_document, spanish_document
from lanctl.shared.language_contract import flatten_document, read_document


def write(tmp_path, document, name="test.lang"):
    path = tmp_path / name
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    return path


def test_v2_roundtrip_preserves_public_keys_and_layout(tmp_path):
    document = _english_document()
    assert document["schemaVersion"] == 2
    assert len(document["LAUNCHERS"]) == 6
    assert all(
        {"CLI", "TUI", "GUI"} <= set(interfaces) <= {"CLI", "TUI", "GUI", "SHARED"}
        for interfaces in document["LAUNCHERS"].values()
    )
    assert LanguageManager(tmp_path).load_file(write(tmp_path, document)).strings == ENGLISH_STRINGS
    assert flatten_document(spanish_document()).keys() == ENGLISH_STRINGS.keys()


@pytest.mark.parametrize("version", [1.2, 2.0, True, "2", None, 0, 3])
def test_schema_is_an_exact_supported_integer(tmp_path, version):
    document = _english_document()
    document["schemaVersion"] = version
    with pytest.raises(ValueError):
        LanguageManager(tmp_path).load_file(write(tmp_path, document))


@pytest.mark.parametrize(
    "text",
    [
        "[]",
        "null",
        '{"schemaVersion":1,"schemaVersion":2}',
        '{"schemaVersion":1,"meta":{"code":"es"},"strings":{"LANCTL.TEST.LABEL":"a","LANCTL.TEST.LABEL":"b"}}',
    ],
)
def test_invalid_json_shape_and_duplicate_members_are_rejected(text):
    with pytest.raises(ValueError):
        read_document(text)


def test_duplicate_public_key_across_sections_is_rejected(tmp_path):
    document = _english_document()
    document["LAUNCHERS"]["LANCTL"]["CLI"]["LANCTL.COMMON.ACTION.LIST"] = "List"
    with pytest.raises(ValueError, match="Duplicate translation key"):
        LanguageManager(tmp_path).load_file(write(tmp_path, document))


@pytest.mark.parametrize(
    "damage",
    [
        "inventory",
        "unknown-interface",
        "unknown-launcher",
        "flat-v2",
        "null-value",
        "unsafe-field",
        "missing-field",
    ],
)
def test_v2_rejects_ambiguous_or_unsafe_documents(tmp_path, damage):
    document = _english_document()
    if damage == "inventory":
        document.update(documentType="LANCTL.P100.StringInventory", installable=False)
    elif damage == "unknown-interface":
        document["LAUNCHERS"]["LANIP"]["WEB"] = {}
    elif damage == "unknown-launcher":
        document["LAUNCHERS"]["UNKNOWN"] = {}
    elif damage == "flat-v2":
        document["strings"] = {}
    elif damage == "null-value":
        document["SHARED"]["LANCTL.COMMON.ACTION.LIST"] = None
    else:
        document["SHARED"]["LANCTL.LANGUAGE.ERROR.NOT_FOUND"] = (
            "{language.__class__}" if damage == "unsafe-field" else "Missing language"
        )
    with pytest.raises(ValueError):
        LanguageManager(tmp_path).load_file(write(tmp_path, document))


def test_v1_custom_catalog_survives_new_templates_and_runtime_fallback(tmp_path):
    document = {
        "schemaVersion": 1,
        "meta": {"code": "es", "name": "Spanish"},
        "strings": {"LANCTL.COMMON.ACTION.LIST": "Lista personalizada"},
    }
    path = write(tmp_path, document, "custom.lang")
    before = path.read_bytes()
    manager = LanguageManager(tmp_path)
    manager.initialize("es")
    assert manager.translate("LANCTL.COMMON.ACTION.LIST") == "Lista personalizada"
    key = "LANCTL.UI.TEXT.NO_PROJECT"
    assert manager.translate(key) == ENGLISH_STRINGS[key]
    assert manager.presentation_payload()["strings"][key] == ENGLISH_STRINGS[key]
    assert path.read_bytes() == before
    exported = manager.export_template(tmp_path / "template.lang")
    assert json.loads(exported.read_text())["schemaVersion"] == 2


def test_regional_fallback_and_literal_interpolated_values(tmp_path):
    manager = LanguageManager(tmp_path / "installed")
    manager.initialize()
    spanish = spanish_document()
    manager.install(write(tmp_path, spanish, "es-input.lang"))
    regional = {"schemaVersion": 1, "meta": {"code": "es-mx", "name": "Regional"}, "strings": {}}
    manager.install(write(tmp_path, regional, "mx-input.lang"))
    manager.select("es-mx")
    assert manager.translate("LANCTL.COMMON.ACTION.LIST") == "Listar"
    original = "{raw}<tag>127.0.0.1 C:\\credentials"
    assert manager.translate("LANCTL.LANGUAGE.ERROR.NOT_FOUND", language=original).endswith(
        original
    )
    assert manager.presentation_payload()["code"] == "es-mx"


def test_bundled_catalogs_match_generated_sources(tmp_path):
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    manager = LanguageManager(tmp_path)
    for filename, expected in (("english", _english_document()), ("spanish", spanish_document())):
        path = root / f"bundled/languages/{filename}.lang"
        assert json.loads(path.read_text()) == expected
        assert manager.load_file(path).strings == flatten_document(expected)


def test_generated_frontend_and_catalog_outputs_are_current():
    import runpy
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    outputs = runpy.run_path(str(root / "tools/generate_language_catalogs.py"))["outputs"]()
    for path, expected in outputs.items():
        assert path.read_text(encoding="utf-8") == expected


def test_all_explicit_consumers_have_catalog_keys(monkeypatch):
    import runpy
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "tools"))
    outputs = runpy.run_path(str(root / "tools/audit_language_usage.py"))["audit"]()
    report = json.loads(outputs[root / "docs/P100-PRELIMINARY-REVIEW.json"])
    assert report["missingConsumerKeys"] == []
    assert report["catalogKeysMatch"]
    assert report["placeholderMismatches"] == []


def test_legacy_empty_translation_has_consistent_frontend_fallback(tmp_path):
    key = "LANCTL.COMMON.ACTION.LIST"
    write(tmp_path, {"schemaVersion": 1, "meta": {"code": "es"}, "strings": {key: ""}})
    manager = LanguageManager(tmp_path)
    manager.initialize("es")
    assert manager.translate(key) == ENGLISH_STRINGS[key]
    assert manager.presentation_payload()["strings"][key] == ENGLISH_STRINGS[key]


def test_duplicate_english_catalogs_are_rejected(tmp_path):
    write(tmp_path, _english_document(), "english.lang")
    write(tmp_path, _english_document(), "another.lang")
    with pytest.raises(ValueError, match="Duplicate installed language code"):
        LanguageManager(tmp_path).initialize()
