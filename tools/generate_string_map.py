"""Generate a language-neutral P100 working map from the static CSV snapshot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/P100-STRING-INVENTORY.csv"
OUTPUT = ROOT / "docs/P100-STRING-MAP.lang"


def build_inventory(source: bytes) -> dict:
    groups = {}
    identifiers = set()
    rows = list(csv.DictReader(io.StringIO(source.decode("utf-8"), newline="")))
    for index, row in enumerate(rows, 1):
        # Include row number to distinguish even identical occurrences in the snapshot.
        identity = json.dumps([index, row], ensure_ascii=False, sort_keys=True)
        identifier = "P100.STRING." + hashlib.sha256(identity.encode()).hexdigest()[:24].upper()
        if identifier in identifiers:
            raise ValueError("Duplicate provisional inventory identifier")
        identifiers.add(identifier)
        group = groups.setdefault(row["launcher"], {}).setdefault(row["interface"], {})
        group[identifier] = {
            "inventoryRow": index,
            "sourceText": row["text"],
            "existingKey": row["key"] or None,
            "targetKey": None,
            "decision": "pending",
            "classificationHint": row["classification"],
            "context": row["context"],
            "kind": row["kind"],
            "source": {
                "file": row["file"],
                "line": int(row["line"]),
                "column": int(row["column"]),
                "sha256": row["source_sha256"],
            },
        }
    return {
        "schemaVersion": 1,
        "documentType": "LANCTL.P100.StringInventory",
        "installable": False,
        "meta": {
            "code": None,
            "name": "P100 preliminary string map",
            "nativeName": None,
            "region": None,
            "version": "1.0",
            "author": "LANCTL",
        },
        "inventory": {
            "source": str(SOURCE.relative_to(ROOT)),
            "sha256": hashlib.sha256(source).hexdigest(),
            "occurrences": len(rows),
            "identifierScope": "provisional; valid for this CSV snapshot only",
            "decisions": ["pending", "translate", "technical", "reuse", "exclude"],
        },
        "launchers": groups,
    }


def build_documents(source: bytes) -> tuple[dict, dict]:
    inventory = build_inventory(source)
    launchers = {
        name: {interface: {} for interface in ("CLI", "TUI", "GUI")}
        for name in ("LANCTL", "LANIP", "LANWIRE", "LANRACK", "LANACCESS", "LANMON")
    }
    pending = {}
    entries = {}
    for owner, interfaces in inventory["launchers"].items():
        for interface, strings in interfaces.items():
            if owner in launchers and interface in launchers[owner]:
                destination = launchers[owner][interface]
                section = "LAUNCHERS"
            else:
                destination = pending.setdefault(owner, {}).setdefault(interface, {})
                section = "PENDING_ASSIGNMENT"
            for identifier, entry in strings.items():
                destination[identifier] = entry["sourceText"]
                entries[identifier] = {
                    "mapLocation": [section, owner, interface, identifier],
                    **entry,
                }
    mapping = {
        "schemaVersion": 2,
        "documentType": "LANCTL.P100.StringInventory",
        "installable": False,
        "meta": inventory["meta"],
        "LAUNCHERS": launchers,
        "PENDING_ASSIGNMENT": pending,
    }
    metadata = {
        "schemaVersion": 2,
        "documentType": "LANCTL.P100.StringInventorySources",
        "inventory": inventory["inventory"],
        "entries": entries,
    }
    return mapping, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = SOURCE.read_bytes()
    mapping, metadata = build_documents(source)
    outputs = {
        OUTPUT: mapping,
        ROOT / "docs/P100-STRING-MAP-SOURCES.json": metadata,
    }
    serialized = {
        path: (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()
        for path, document in outputs.items()
    }
    # Validate all outputs before writing. Only migrate an unannotated v1 map.
    for path, content in serialized.items():
        if args.check:
            if not path.exists() or path.read_bytes() != content:
                raise SystemExit(f"P100 string map differs: {path.name}")
        elif (
            path.exists()
            and path.read_bytes() != content
            and (path != OUTPUT or json.loads(path.read_bytes()) != build_inventory(source))
        ):
            raise SystemExit(f"Existing map differs: preserve/reconcile annotations in {path.name}")
    if not args.check:
        for path, content in serialized.items():
            path.write_bytes(content)
    print("P100 string map: current" if args.check else "P100 string map: generated")


if __name__ == "__main__":
    main()
