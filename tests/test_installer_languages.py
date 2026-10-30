"""Installer language choices use validated shipped catalogs and preserve upgrades."""

import json
import re
import runpy
import shutil
from pathlib import Path

import pytest
from test_installation_preferences import data as data

from lanctl.core import config
from lanctl.core.installation import initialize_defaults
from lanctl.core.installation_languages import available_languages, install_language
from lanctl.shared.i18n import LanguageManager

ROOT = Path(__file__).resolve().parents[1]
generate = runpy.run_path(str(ROOT / "tools/generate_installer_languages.py"))["generate"]


def test_bundle_and_generated_choices_match():
    manifest, choices = generate(ROOT / "bundled/languages")
    assert manifest == (ROOT / "bundled/languages/catalog.json").read_text()
    assert choices == (ROOT / "packaging/inno/program-languages.iss").read_text()
    assert set(available_languages()) == {"en", "es"}


def test_third_language_is_discovered_offline_and_installed(tmp_path):
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "bundled/languages", bundle)
    document = json.loads((bundle / "spanish.lang").read_text())
    document["meta"].update(code="fr", name="French", nativeName="Français")
    (bundle / "french.lang").write_text(json.dumps(document))
    manifest, choices = generate(bundle)
    (bundle / "catalog.json").write_text(manifest)
    assert "ProgramLanguageCodes.Add('fr')" in choices
    assert "Français" in choices
    installed = tmp_path / "installed"
    install_language("fr", root=bundle, directory=installed)
    manager = LanguageManager(installed)
    manager.initialize("fr")
    assert manager.selected == "fr"


def test_initial_language_effective_on_first_runtime(data):
    result = initialize_defaults(language="es", plugins="none")
    assert result["languageApplied"] and result["language"] == "es"
    assert config.load_config()["language"] == "es"
    manager = LanguageManager()
    manager.initialize(config.load_config()["language"])
    assert manager.selected == "es"
    assert manager.translate("LANCTL.COMMON.ACTION.LIST") == "Listar"


def test_upgrade_preserves_language_until_explicit_change(data):
    initialize_defaults(language="es", theme="forest", plugins="none")
    before = config.CONFIG_PATH.read_bytes()
    preserved = initialize_defaults(language="en", theme="light", plugins="all")
    assert not preserved["languageApplied"]
    assert config.CONFIG_PATH.read_bytes() == before
    changed = initialize_defaults(language="en", change_language=True)
    assert changed["languageApplied"]
    assert config.load_config()["language"] == "en"
    assert config.load_config()["guiPreferences"]["theme"] == "forest"


def test_existing_custom_translation_is_not_overwritten(data):
    initialize_defaults(language="es", plugins="none")
    manager = LanguageManager()
    manager.initialize("es")
    path = manager.catalogs["es"].path
    doc = json.loads(path.read_text())
    doc["SHARED"]["LANCTL.COMMON.ACTION.LIST"] = "Lista personalizada"
    path.write_text(json.dumps(doc))
    before = path.read_bytes()
    initialize_defaults(language="es", change_language=True)
    assert path.read_bytes() == before


def test_invalid_language_cannot_select_uninstalled_translation(data):
    with pytest.raises(ValueError):
        initialize_defaults(language="unavailable")
    assert not config.CONFIG_PATH.exists()
    with pytest.raises(ValueError):
        initialize_defaults(change_language=True)
    assert not config.CONFIG_PATH.exists()


@pytest.mark.parametrize("damage", ["hash", "schema", "path", "placeholder"])
def test_bad_bundle_rejected_before_installation(tmp_path, damage):
    bundle = tmp_path / "bundle"
    shutil.copytree(ROOT / "bundled/languages", bundle)
    path = bundle / "catalog.json"
    manifest = json.loads(path.read_text())
    if damage == "schema":
        manifest["schemaVersion"] = 999
    elif damage == "path":
        manifest["languages"][0]["file"] = "../outside.lang"
    else:
        source = bundle / "spanish.lang"
        doc = json.loads(source.read_text())
        if damage == "hash":
            doc["meta"]["author"] = "tampered"
        else:
            doc["SHARED"]["LANCTL.LANGUAGE.ERROR.NOT_FOUND"] = "Sin parámetro"
        source.write_text(json.dumps(doc))
        if damage == "placeholder":
            with pytest.raises(ValueError):
                generate(bundle)
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        install_language("es", root=bundle, directory=tmp_path / "installed")
    assert not (tmp_path / "installed").exists()


def test_installer_messages_are_complete_and_options_are_bound():
    source = (ROOT / "packaging/inno/LANCTL.iss").read_text()
    messages = (ROOT / "packaging/inno/messages.iss").read_text()
    entries = {lang: {} for lang in ["en", "es"]}
    for line in messages.splitlines():
        match = re.match(r"(en|es)\.([^=]+)=(.*)", line)
        if match:
            entries[match[1]][match[2]] = match[3]
    assert set(entries["en"]) == set(entries["es"])
    used = set(re.findall(r"\{cm:([^},]+)", source)) | set(
        re.findall(r"CustomMessage\('([^']+)'\)", source)
    )
    assert used <= set(entries["en"])
    for key in entries["en"]:
        assert entries["en"][key] and entries["es"][key]
        assert sorted(re.findall(r"%[1-9n]", entries["en"][key])) == sorted(
            re.findall(r"%[1-9n]", entries["es"][key])
        )
    assert "ShowLanguageDialog=yes" in source
    assert "UsePreviousLanguage=yes" in source
    assert "UsePreviousTasks=yes" in source
    install = next(
        line for line in source.splitlines() if 'Parameters: "completions install"' in line
    )
    assert "Tasks: clink" in install and "runasoriginaluser" in install
    remove = next(
        line for line in source.splitlines() if "not WizardIsTaskSelected('clink')" in line
    )
    assert "completions uninstall" in remove and "runasoriginaluser" in remove
    assert "GetPreviousData('ProgramLanguage'" in source
    assert "ProgramLanguageCodes.IndexOf(ActiveLanguage)" in source
    assert " --change-language" in source
    assert "bundled/languages" in (ROOT / "LANCTL.spec").read_text()


def test_real_setup_command_and_first_program_launch(tmp_path):
    import os
    import subprocess
    import sys

    env = dict(
        os.environ,
        LANCTL_DATA_DIR=str(tmp_path / "app"),
        LANCTL_SECRET_DIR=str(tmp_path / "secrets"),
        PYTHONPATH=str(ROOT / "src"),
    )
    env.pop("LANCTL_SESSION_CONTEXT", None)
    result = subprocess.run(
        [sys.executable, "-m", "lanctl", "setup-defaults", "--plugins", "none", "--language", "es"],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout.strip().splitlines()[-1])
    assert output["language"] == "es" and output["languageApplied"]
    # A separate process must resolve the same catalog and chosen preference.
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            "from lanctl.shared.i18n import initialize_language,t; print(initialize_language().selected);print(t('LANCTL.COMMON.ACTION.LIST'))",
        ],
        env=env,
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert probe.stdout.strip().splitlines() == ["es", "Listar"]


def test_custom_catalog_with_same_filename_is_preserved(tmp_path):
    installed = tmp_path / "installed"
    manager = LanguageManager(installed)
    manager.initialize("en")
    document = json.loads((ROOT / "bundled/languages/spanish.lang").read_text())
    document["meta"]["code"] = "xx"
    occupied = installed / "spanish.lang"
    occupied.write_text(json.dumps(document))
    before = occupied.read_bytes()
    with pytest.raises(ValueError, match="filename"):
        install_language("es", directory=installed)
    assert occupied.read_bytes() == before
    assert json.loads((installed / "languajes.json").read_text())["selected"] == "en"
