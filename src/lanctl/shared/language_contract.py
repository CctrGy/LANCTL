"""Versioned language files, independent of UI and user configuration."""

from __future__ import annotations

import json
import re
from string import Formatter

LAUNCHERS = ("LANCTL", "LANIP", "LANWIRE", "LANRACK", "LANACCESS", "LANMON")
INTERFACES = ("CLI", "TUI", "GUI")
KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*){2,}$")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate language JSON member: {key}")
        result[key] = value
    return result


def read_document(text):
    document = json.loads(text, object_pairs_hook=unique_object)
    if not isinstance(document, dict):
        raise ValueError("Language document must be an object")
    version = document.get("schemaVersion")
    if type(version) is not int or version not in (1, 2):
        raise ValueError(f"Unsupported language schema: {version}")
    if document.get("installable") is False or "documentType" in document:
        raise ValueError("An inventory is not an installable language catalog")
    meta = document.get("meta")
    if not isinstance(meta, dict) or not isinstance(meta.get("code"), str):
        raise ValueError("Language metadata must include a language code")
    for field in ("name", "nativeName", "region", "version", "author"):
        if field in meta and not isinstance(meta[field], str):
            raise ValueError(f"Language metadata must be text: {field}")
    return document


def flatten_document(document):
    """Flatten sections without changing public identities or accepting duplicates."""
    result = {}

    def walk(branch):
        if not isinstance(branch, dict):
            raise ValueError("Language section must be an object")
        for key, value in branch.items():
            if KEY_PATTERN.fullmatch(key):
                if not isinstance(value, str):
                    raise ValueError(f"Translation must be text: {key}")
                if key in result:
                    raise ValueError(f"Duplicate translation key: {key}")
                result[key] = value
            elif isinstance(value, dict):
                walk(value)
            else:
                raise ValueError(f"Invalid translation key: {key}")

    if document["schemaVersion"] == 1:
        strings = document.get("strings")
        if not isinstance(strings, dict):
            raise ValueError("Language schema v1 requires strings")
        for key, value in strings.items():
            if not KEY_PATTERN.fullmatch(key) or not isinstance(value, str):
                raise ValueError(f"Invalid translation key or value: {key}")
        result.update(strings)
    else:
        if set(document) - {"schemaVersion", "meta", "SHARED", "LAUNCHERS"}:
            raise ValueError("Unknown language schema v2 section")
        if "strings" in document or "launchers" in document:
            raise ValueError("Language schema v2 requires SHARED/LAUNCHERS sections")
        if "SHARED" in document:
            walk(document["SHARED"])
        launchers = document.get("LAUNCHERS")
        if not isinstance(launchers, dict):
            raise ValueError("Language schema v2 requires LAUNCHERS")
        for launcher, interfaces in launchers.items():
            if launcher not in LAUNCHERS or not isinstance(interfaces, dict):
                raise ValueError(f"Invalid language launcher: {launcher}")
            for interface, strings in interfaces.items():
                if interface not in (*INTERFACES, "SHARED"):
                    raise ValueError(f"Invalid language interface: {interface}")
                walk(strings)
    return result


def placeholders(value):
    fields = set()
    for _, field, specification, conversion in Formatter().parse(value):
        if field is None:
            continue
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", field):
            raise ValueError(f"Unsafe translation placeholder: {field}")
        if "{" in specification or "}" in specification or conversion not in (None, "s", "r", "a"):
            raise ValueError(f"Unsupported translation placeholder: {field}")
        fields.add(field)
    return fields


def structured_document(meta, strings, locations=None):
    document = {
        "schemaVersion": 2,
        "meta": dict(meta),
        "SHARED": {},
        "LAUNCHERS": {
            launcher: {interface: {} for interface in INTERFACES} for launcher in LAUNCHERS
        },
    }
    locations = locations or {}
    for key, value in strings.items():
        location = locations.get(key)
        if location:
            launcher, interface = location
            document["LAUNCHERS"][launcher].setdefault(interface, {})[key] = value
        else:
            document["SHARED"][key] = value
    return document
