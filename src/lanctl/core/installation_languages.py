"""Validated, offline language catalog shipped with this exact distribution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from lanctl.core.resources import bundled_path
from lanctl.shared.i18n import LanguageManager


def available_languages(root=None):
    root = Path(root) if root is not None else bundled_path("bundled/languages")
    manifest = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    if (
        not isinstance(manifest, dict)
        or manifest.get("schemaVersion") != 1
        or not isinstance(manifest.get("languages"), list)
    ):
        raise ValueError("Invalid installation language manifest")
    result = {}
    validator = LanguageManager(root)
    for entry in manifest["languages"]:
        if not isinstance(entry, dict) or set(entry) != {"file", "sha256", "code", "nativeName"}:
            raise ValueError("Invalid installation language entry")
        if not all(isinstance(value, str) for value in entry.values()):
            raise ValueError("Installation language metadata must be text")
        filename = entry["file"]
        if Path(filename).name != filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid installation language filename")
        source = root / filename
        if source.is_symlink() or source.resolve().parent != root.resolve():
            raise ValueError("Installation language must be a regular bundled file")
        if hashlib.sha256(source.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError("Installation language checksum mismatch")
        catalog = validator.load_file(source)
        if catalog.code != entry["code"] or catalog.code in result:
            raise ValueError("Invalid or duplicate installation language code")
        if catalog.native_name != entry["nativeName"]:
            raise ValueError("Installation language metadata mismatch")
        result[catalog.code] = catalog
    if "en" not in result:
        raise ValueError("The installation language bundle must include English")
    return result


def install_language(code, *, root=None, directory=None):
    catalogs = available_languages(root)
    if code not in catalogs:
        raise ValueError(f"Language not included in this distribution: {code}")
    manager = LanguageManager(directory)
    manager.initialize("en")
    catalog = catalogs[code]
    current = manager.catalogs.get(code)
    # Preserve installed/custom translations; select them only after validation.
    if current is None or current.path is None:
        manager.install(catalog.path)
    manager.select(code)
    return {"code": code, "preservedCatalog": bool(current and current.path)}
