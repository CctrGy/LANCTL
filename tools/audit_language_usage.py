"""Audit explicit language consumers and English/Spanish files without running LANCTL."""

from __future__ import annotations

import argparse
import ast
import csv
import io
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from generate_string_inventory import collect  # noqa: E402

from lanctl.shared.i18n import ENGLISH_STRINGS, LanguageManager  # noqa: E402
from lanctl.shared.language_contract import placeholders  # noqa: E402


def html_bindings(source):
    positions = set()

    class Bindings(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []

        def handle_starttag(self, tag, attrs):
            self.stack.append((tag, dict(attrs)))

        def handle_endtag(self, tag):
            if any(item[0] == tag for item in self.stack):
                while self.stack and self.stack.pop()[0] != tag:
                    pass

        def handle_data(self, data):
            if self.stack and "data-i18n" in self.stack[-1][1]:
                line, column = self.getpos()
                positions.add((line, column + 1))

    Bindings().feed(source)
    return positions


def review_disposition(row, source, tree):
    """Explain exclusions at their actual AST/HTML location; never infer coverage."""
    if "prototype" in row["file"]:
        return "DESIGN_PREVIEW", "Design/demo surface, outside production launchers"
    if row["kind"] == "html-attribute":
        context = row["context"]
        attribute = context.split("@", 1)[-1]
        lines = source.splitlines()
        if "data-i18n-" + attribute in lines[row["line"] - 1]:
            return "EXPLICIT_BINDING", "Translated through an explicit attribute binding"
    neutral = {
        "LANCTL",
        "LANIP",
        "LANWIRE",
        "LANRACK",
        "LANACCESS",
        "LANMON",
        "LAN",
        "IP",
        "MAC",
        "CNF",
        "IDF",
        "CTL",
        "ACCESS",
        "Web",
        "GitHub",
        "O",
        "X",
        "S",
        "F",
        "-",
        "—",
        "\u00d7",
        "ms",
        " switches",
        "Ctrl K",
        "\u203a_ CLI",
        "● GUI",
        "⌂ LANCTL",
        " LANIP · LANCTL ",
        "LANCTL_DATA_DIR",
    }
    if row["text"] in neutral:
        return "TECHNICAL_OR_NAME", "Product/protocol/schema identifier, unit or keyboard notation"
    # Explicitly reviewed residuals: stable command syntax, schema and raw diagnostics.
    text = row["text"]
    if text in {
        "LANLAB",
        "LANACCESS> ",
        "LANMON> ",
        "LANWIRE> ",
        "> ",
        "DRY-RUN",
        "-description",
        "\uff0b",
        "⌕",
        "↶",
        "↷",
        "0",
        "●",
    }:
        return "TECHNICAL_OR_NAME", "Stable prompt/command token, product name, icon or counter"
    if text in {"description", "help", "settings", "info"}:
        return "SCHEMA_KEY", "Fixed metadata field or internal modal selector"
    if row["context"] == "SaveModeDefinition":
        return (
            "TRANSLATED_METADATA",
            "Original domain metadata; translated at CLI/GUI presentation boundary",
        )
    if text in {
        'f"política aislada: {event}: {detail}"',
        "TCP/445 no accesible",
        "se requiere autenticación",
    } and row["file"].endswith(("plugins/process_runtime.py", "plugins/smb_runtime.py")):
        return (
            "ORIGINAL_DIAGNOSTIC",
            "Original isolated-worker/SMB error record retained with its origin",
        )
    if row["kind"] == "python-fstring":
        if row["file"].endswith(("manager_cli.py", "interactive_console.py")):
            return "TECHNICAL_OR_NAME", "Product/version and executable command names"
        if row["file"].endswith("commands/ssh.py"):
            return (
                "EXPLICIT_BINDING",
                "Protocol/port prefix with explicitly translated availability values",
            )
        if row["file"].endswith("plugins/declarative_commands.py"):
            return "FORMATTED_DATA_OR_SCHEMA", "Fixed CNF state codes and their counters"
        if row["file"].endswith("tui/main.py"):
            return (
                "EXPLICIT_BINDING",
                "Modal title assembled from translated title, tab and editing labels",
            )
    if tree is not None:
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        node = next(
            (
                node
                for node in ast.walk(tree)
                if getattr(node, "lineno", None) == row["line"]
                and getattr(node, "col_offset", -1) + 1 == row["column"]
                and isinstance(node, (ast.Constant, ast.JoinedStr))
            ),
            None,
        )
        chain = []
        current = node
        while current in parents:
            current = parents[current]
            chain.append(current)
        if any(
            isinstance(parent, ast.Call)
            and any(
                token in ast.unparse(parent.func).lower()
                for token in ("errors.", "logger.", "logging.", "write_log")
            )
            for parent in chain
        ):
            return (
                "ORIGINAL_DIAGNOSTIC",
                "Original structured error/log record; preserve content and origin",
            )
        if any(isinstance(parent, ast.FormattedValue) for parent in chain):
            return (
                "FORMATTED_DATA_OR_SCHEMA",
                "Value expression, formatting spec or fixed schema column identifier",
            )
        if node is not None and isinstance(node, ast.JoinedStr):
            literal = "".join(item.value for item in node.values if isinstance(item, ast.Constant))
            literal = re.sub(r"\[[^]]*\]", "", literal)
            words = set(re.findall(r"[A-Za-z]+", literal))
            tokens = {
                "LANCTL",
                "LANIP",
                "LANWIRE",
                "LANRACK",
                "LANACCESS",
                "LANMON",
                "CLI",
                "TUI",
                "IP",
                "MAC",
                "CNF",
                "UUID",
                "SHA",
                "TCP",
                "TTL",
                "U",
                "s",
                "ms",
                "ERROR",
                "INFO",
                "HELP",
                "PLAN",
                "CISCO",
                "TYPES",
                "OWNER",
                "TYPE",
                "VERSION",
                "STATE",
                "PATH",
                "SIZE",
                "COMPRESSED",
                "ID",
                "sel",
                "id",
                "alias",
                "native",
                "label",
                "cnf",
                "protocols",
                "command",
                "phase",
                "start",
                "end",
                "code",
                "elapsed",
                "diagnostic",
                "CorrelationId",
                "RunId",
                "TaskId",
                "OperationId",
            }
            if not words or words <= tokens or literal.startswith("radmin://"):
                return (
                    "FORMATTED_DATA_OR_SCHEMA",
                    "Raw values, protocol/CLI identity, format markup or URI",
                )
        if node is not None and isinstance(parents.get(node), ast.Subscript):
            return "SCHEMA_KEY", "Lookup key in structured data, not display text"
    return "REVIEW", "Requires semantic review; not automatically a missing translation"


def audit():
    references, dynamic, residual = [], [], []
    paths = (
        sorted((ROOT / "src/lanctl").rglob("*.py"))
        + sorted((ROOT / "gui").glob("*.js"))
        + sorted((ROOT / "gui").glob("*.html"))
    )
    for path in paths:
        relative = str(path.relative_to(ROOT))
        if path.name in ("ui_messages.py", "i18n-defaults.js"):
            continue
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source) if path.suffix == ".py" else None
        if path.suffix == ".py":
            for node in ast.walk(tree):
                if (
                    not isinstance(node, ast.Call)
                    or not isinstance(node.func, ast.Name)
                    or node.func.id != "t"
                    or not node.args
                ):
                    continue
                argument = node.args[0]
                if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
                    references.append(
                        {"file": relative, "line": node.lineno, "key": argument.value}
                    )
                else:
                    dynamic.append(
                        {"file": relative, "line": node.lineno, "expression": ast.unparse(argument)}
                    )
        else:
            pattern = r'(?:LanctlI18n\.(?:t|html)\(\s*|data-i18n(?:-[\w-]+)?=)["\x27](LANCTL\.[A-Z0-9_.]+)'
            # bindText's first argument is a DOM expression, its second is the key.
            pattern += r'|LanctlI18n\.(?:bindText|bindAttribute)\([^;\n]*?["\x27](LANCTL\.[A-Z0-9_.]+)["\x27]'
            for match in re.finditer(pattern, source):
                references.append(
                    {
                        "file": relative,
                        "line": source.count("\n", 0, match.start()) + 1,
                        "key": match.group(1) or match.group(2),
                    }
                )
        bound = html_bindings(source) if path.suffix == ".html" else set()
        for row in collect(path):
            if row["classification"] == "UI_CANDIDATE":
                # Keep unbound siblings on the same line in the residual inventory.
                if row["kind"] == "html-text" and (row["line"], row["column"]) in bound:
                    continue
                disposition, reason = review_disposition(row, source, tree)
                residual.append({**row, "reviewDisposition": disposition, "reviewReason": reason})
    manager = LanguageManager(ROOT / "bundled/languages")
    english = manager.load_file(ROOT / "bundled/languages/english.lang")
    spanish = manager.load_file(ROOT / "bundled/languages/spanish.lang")
    missing = [reference for reference in references if reference["key"] not in english.strings]
    keys_match = english.strings.keys() == spanish.strings.keys() == ENGLISH_STRINGS.keys()
    mismatches = [
        key
        for key in english.strings.keys() & spanish.strings.keys()
        if placeholders(english.strings[key]) != placeholders(spanish.strings[key])
    ]
    if missing or not keys_match or mismatches:
        raise ValueError(
            f"Language audit failed: missing={missing}, keys_match={keys_match}, placeholders={mismatches}"
        )
    report = {
        "scope": "Static explicit consumers and bundled catalogs; not full functional coverage",
        "sourceFilesExamined": len(paths),
        "catalogKeysPerLanguage": len(english.strings),
        "catalogKeysMatch": keys_match,
        "placeholderMismatches": mismatches,
        "missingConsumerKeys": missing,
        "explicitConsumerReferences": len(references),
        "referencedUniqueKeys": len({item["key"] for item in references}),
        "unreferencedOrDynamicOnlyKeys": sorted(
            set(english.strings) - {item["key"] for item in references}
        ),
        "dynamicReferencesRequiringReview": dynamic,
        "residualPythonHtmlCandidates": len(residual),
        "residualDispositions": dict(
            sorted(Counter(row["reviewDisposition"] for row in residual).items())
        ),
        "unclassifiedCandidates": sum(row["reviewDisposition"] == "REVIEW" for row in residual),
        "residualByOwner": dict(sorted(Counter(row["launcher"] for row in residual).items())),
        "limitations": [
            "Residual candidates can be technical data; they are not approved translations.",
            "Frontend dynamic strings and templates require semantic review; this is not a JS AST audit.",
            "HTML bindings are checked at text-node positions; runtime-generated content still needs review.",
            "Dynamic Python keys require separate validation of their generated sets.",
        ],
        "references": references,
    }
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(residual[0]) if residual else ["file"])
    writer.writeheader()
    writer.writerows(residual)
    return {
        ROOT / "docs/P100-PRELIMINARY-REVIEW.json": json.dumps(report, ensure_ascii=False, indent=2)
        + "\n",
        ROOT / "docs/P100-RESIDUAL-STRINGS.csv": stream.getvalue(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for path, content in audit().items():
        if args.check:
            if not path.exists() or path.read_bytes() != content.encode():
                raise SystemExit(f"Stale language audit: {path.name}")
        else:
            path.write_bytes(content.encode())
    print("Language audit: consumers and bilingual catalogs validated; residuals documented")


if __name__ == "__main__":
    main()
