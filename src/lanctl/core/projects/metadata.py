"""Atomic, optimistic edits of project identity and LAN descriptive metadata."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from lanctl.core.file_transaction import transactional_path_argument
from lanctl.core.projects import vlf
from lanctl.core.projects.settings import project_settings

FIELDS = (
    ("name", "Nombre", "identity", "name"),
    ("description", "Descripción", "identity", "description"),
    ("author", "Autor", "identity", "author"),
    ("lan", "LAN", "lan", "name"),
    ("location", "Ubicación", "lan", "location"),
    ("company", "Empresa", "lan", "company"),
    ("responsible", "Responsable", "lan", "responsible"),
)


def _snapshot(documents):
    values = {name: documents[section].get(key, "") for name, _, section, key in FIELDS}
    revision = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
    return {"values": values, "revision": revision}


def read_metadata(path):
    return _snapshot(project_settings(path))


def validate_metadata(values):
    if not isinstance(values, dict) or set(values) != {name for name, *_ in FIELDS}:
        raise ValueError("Metadatos de proyecto desconocidos o incompletos")
    if any(
        not isinstance(value, str) or len(value) > 4096 or "\x00" in value
        for value in values.values()
    ):
        raise ValueError("Los metadatos requieren texto de hasta 4096 caracteres")
    if not values["name"].strip():
        raise ValueError("El nombre del proyecto no puede estar vacío")
    return {key: value.strip() for key, value in values.items()}


@transactional_path_argument("path", transform=lambda value: vlf._vlf_path(value))
def update_metadata(path, values, revision):
    values = validate_metadata(values)
    source = vlf._existing_vlf(path)
    documents = project_settings(source)
    if revision != _snapshot(documents)["revision"]:
        raise ValueError("Los metadatos cambiaron en otra ventana; recarga antes de guardar")
    for name, _, section, key in FIELDS:
        documents[section][key] = values[name].strip()
    with vlf._VLF_WRITE_LOCK, tempfile.TemporaryDirectory(prefix="lanctl-metadata-") as temporary:
        root = Path(temporary)
        with vlf._safe_archive(source) as archive:
            for entry in archive.infolist():
                if entry.is_dir():
                    continue
                target = root / entry.filename
                if not target.resolve().is_relative_to(root.resolve()):
                    raise ValueError("Ruta de proyecto fuera del contenedor")
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(entry) as stream, target.open("wb") as output:
                    shutil.copyfileobj(stream, output)
        vlf._write_json(root / "lan/lanIdentifier.info", documents["lan"])
        info = documents["identity"]
        info["updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
        info["contentHash"] = vlf._hash_directory(root, {"project.info", "meta/checksum"})
        vlf._write_json(root / "project.info", info)
        vlf._write_json(
            root / "meta/checksum",
            {
                "algorithm": "SHA-256",
                "hash": vlf._hash_directory(root, {"meta/checksum"}),
                "scope": "all files except meta/checksum",
                "contentHash": info["contentHash"],
            },
        )
        from lanctl.core.persistence import create_backup

        create_backup(source, directory=source.parent / ".lanctl-backups")
        vlf._write_archive(root, source)
    from lanctl.core.projects.catalog import ProjectCatalog
    from lanctl.core.session import current_session

    ProjectCatalog().register(source)
    if session := current_session():
        session.emit(
            "LANCTL.Core.Storage.Changed", project=str(source), metadata={"path": str(source)}
        )
    return _snapshot(documents)
