from pathlib import Path

from lanctl.core.projects.catalog import ProjectCatalog


def test_catalog_discovers_default_projects_before_external_and_persists(tmp_path: Path) -> None:
    documents = tmp_path / "Documents" / "LanCTL"
    external = tmp_path / "shared" / "remote.vlf"
    documents.mkdir(parents=True)
    external.parent.mkdir()
    (documents / "local.vlf").write_bytes(b"not-a-vlf-yet")
    external.write_bytes(b"not-a-vlf-yet")
    database = tmp_path / "state" / "projects.db"

    catalog = ProjectCatalog(database)
    catalog.register(external)
    entries = catalog.refresh(documents)

    assert [entry.path.name for entry in entries] == ["local.vlf", "remote.vlf"]
    assert entries[0].in_default_directory is True
    assert entries[1].in_default_directory is False
    assert all(entry.available for entry in entries)
    assert ProjectCatalog(database).list(documents) == entries


def test_catalog_keeps_missing_external_project_until_removed(tmp_path: Path) -> None:
    documents = tmp_path / "Documents" / "LanCTL"
    external = tmp_path / "elsewhere" / "old.vlf"
    external.parent.mkdir()
    external.write_bytes(b"project")
    catalog = ProjectCatalog(tmp_path / "projects.db")
    catalog.register(external)
    external.unlink()

    entries = catalog.refresh(documents)
    assert len(entries) == 1
    assert entries[0].available is False

    catalog.remove(external, delete_file=True)
    assert catalog.list(documents) == []


def test_catalog_remove_can_delete_project_file(tmp_path: Path) -> None:
    documents = tmp_path / "Documents" / "LanCTL"
    project = documents / "delete-me.vlf"
    documents.mkdir(parents=True)
    project.write_bytes(b"project")
    catalog = ProjectCatalog(tmp_path / "projects.db")
    catalog.register(project)

    catalog.remove(project, delete_file=True)

    assert not project.exists()
    assert catalog.list(documents) == []
