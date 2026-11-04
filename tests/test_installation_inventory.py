"""Cleanup plans are scoped by trusted roots and preserve changed/foreign files."""

import json

import pytest

from lanctl.core.installation_inventory import (
    plan_owned_file_cleanup,
    record_installed_file,
    write_installed_file,
)


def test_inventory_tracks_only_owned_unchanged_files_and_never_deletes(tmp_path):
    root = tmp_path / "applications"
    root.mkdir()
    owned, edited, foreign = [root / name for name in ("owned", "edited", "foreign")]
    for path in (owned, edited, foreign):
        path.write_text("initial")
    manifest = tmp_path / "inventory.json"
    for path in (owned, edited):
        record_installed_file(manifest, root, path)
    edited.write_text("user changes")
    plan = plan_owned_file_cleanup(manifest, allowed_roots=[root])
    assert plan["removable"] == [str(owned)]
    assert plan["preserved"] == [str(edited)]
    assert foreign.read_text() == "initial" and owned.exists()


def test_tampered_path_and_symlink_are_never_removable(tmp_path):
    root = tmp_path / "owned"
    root.mkdir()
    target = root / "resource"
    target.write_text("ours")
    foreign = tmp_path / "foreign"
    foreign.write_text("private")
    manifest = tmp_path / "inventory.json"
    record_installed_file(manifest, root, target)
    document = json.loads(manifest.read_text())
    document["files"].append({**document["files"][0], "relative": "../foreign"})
    manifest.write_text(json.dumps(document))
    target.unlink()
    target.symlink_to(foreign)
    plan = plan_owned_file_cleanup(manifest, allowed_roots=[root])
    assert len(plan["unsafe"]) == 2
    assert not plan["removable"]
    assert foreign.read_text() == "private"


def test_invalid_inventory_and_wrong_root_fail_closed(tmp_path):
    manifest = tmp_path / "inventory.json"
    manifest.write_text('{"schemaVersion":999,"files":[]}')
    with pytest.raises(ValueError):
        plan_owned_file_cleanup(manifest, allowed_roots=[tmp_path])
    assert json.loads(manifest.read_text())["schemaVersion"] == 999


def test_upgrade_preserves_foreign_and_user_edited_files(tmp_path):
    root = tmp_path / "applications"
    root.mkdir()
    manifest, target = tmp_path / "inventory.json", root / "launcher.desktop"
    target.write_text("unrelated content")
    with pytest.raises(ValueError):
        write_installed_file(manifest, root, target, "LANCTL shortcut")
    assert target.read_text() == "unrelated content"
    target.unlink()
    write_installed_file(manifest, root, target, "LANCTL shortcut")
    write_installed_file(manifest, root, target, "LANCTL upgraded shortcut")
    assert target.read_text() == "LANCTL upgraded shortcut"
    target.write_text("custom user edits")
    with pytest.raises(ValueError):
        write_installed_file(manifest, root, target, "replacement")
    assert target.read_text() == "custom user edits"


@pytest.mark.parametrize("corruption", ["oversize", "nesting", "digest", "duplicate"])
def test_manifest_limits_and_schema_errors_preserve_files(tmp_path, corruption):
    from lanctl.core.installation_inventory import MAX_INVENTORY_BYTES

    root = tmp_path / "applications"
    root.mkdir()
    manifest, target = tmp_path / "inventory.json", root / "resource"
    write_installed_file(manifest, root, target, "owned")
    document = json.loads(manifest.read_text())
    if corruption == "oversize":
        manifest.write_bytes(b" " * (MAX_INVENTORY_BYTES + 1))
    elif corruption == "nesting":
        manifest.write_text("[" * 2000 + "]" * 2000)
    else:
        if corruption == "digest":
            document["files"][0]["sha256"] = "invalid"
        else:
            document["files"].append(dict(document["files"][0]))
        manifest.write_text(json.dumps(document))
    before = manifest.read_bytes()
    with pytest.raises(ValueError):
        plan_owned_file_cleanup(manifest, allowed_roots=[root])
    assert target.read_text() == "owned"
    assert manifest.read_bytes() == before


def test_capacity_check_happens_before_writing_resource(tmp_path, monkeypatch):
    from lanctl.core import installation_inventory

    manifest, target = tmp_path / "inventory.json", tmp_path / "resource"
    monkeypatch.setattr(installation_inventory, "MAX_INVENTORY_FILES", 0)
    with pytest.raises(ValueError):
        write_installed_file(manifest, tmp_path, target, "owned")
    assert not target.exists()
    assert not manifest.exists()
