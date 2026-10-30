"""Static, conservative P100 inventory; no application imports or user data reads."""

from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = (
    "file",
    "line",
    "column",
    "launcher",
    "interface",
    "kind",
    "classification",
    "context",
    "key",
    "text",
    "source_sha256",
)
APPS = {
    "ip": "LANIP",
    "wire": "LANWIRE",
    "rack": "LANRACK",
    "access": "LANACCESS",
    "monitor": "LANMON",
    "suite": "LANCTL",
}


def scope(path):
    parts = path.parts
    launcher = "SHARED"
    interface = "SHARED"
    if "apps" in parts:
        launcher = APPS.get(parts[parts.index("apps") + 1], "SHARED")
    if "bootstrap" in parts and path.stem in (
        "lanctl",
        "lanip",
        "lanwire",
        "lanrack",
        "lanaccess",
        "lanmon",
    ):
        launcher = path.stem.upper()
    str(path)
    if parts[0] == "plugins-src":
        return parts[1], "PLUGIN"
    if parts[0] == "packaging":
        return "INSTALLER", "INSTALLER"
    if parts[0] == "bundled":
        return "SHARED", "CATALOG"
    if parts[0] == "gui":
        interface = "GUI"
        if path.name.startswith(("suite",)):
            launcher = "LANCTL"
        elif (
            path.name.startswith(("lanip", "device-sheet", "first-scan"))
            or path.name == "index.html"
        ):
            launcher = "LANIP"
        elif path.name.startswith("wire-"):
            launcher = "LANWIRE"
        elif path.name.startswith("rack-"):
            launcher = "LANRACK"
        elif path.name.startswith("monitor-"):
            launcher = "LANMON"
        # Templates/modules shared by several launchers retain SHARED ownership.
    elif "tui" in parts or "tui" in path.stem or path.stem == "terminal_ui":
        interface = "TUI"
    elif "gui" in parts or "gui" in path.stem:
        interface = "GUI"
    elif (
        path.name in ("interfaces.py", "manager_cli.py")
        or str(path).endswith("apps/rack/cli.py")
        or path.stem == "interactive_console"
    ):
        interface = "CLI/TUI"
    elif "cli" in parts or "cli" in path.stem or "bootstrap" in parts:
        interface = "CLI"
    if "prototypes" in parts or "prototype" in path.name:
        interface += ":PROTOTYPE"
    return launcher, interface


def collect(path):
    source = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT)
    launcher, interface = scope(relative)
    digest = hashlib.sha256(source.encode()).hexdigest()
    rows = []

    def add(line, column, kind, text, context="", classification="REVIEW", key=""):
        if not text.strip():
            return
        if re.fullmatch(r"[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*){2,}", text):
            classification, key = "KEY_REFERENCE", text
        rows.append(
            dict(
                zip(
                    FIELDS,
                    (
                        str(relative),
                        line,
                        column,
                        launcher,
                        interface,
                        kind,
                        classification,
                        context,
                        key,
                        text,
                        digest,
                    ),
                )
            )
        )

    if path.suffix == ".py" or path.name == "main.exec":
        tree = ast.parse(source, filename=str(relative))
        parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
        docstrings = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
            ):
                docstrings.add(node.body[0].value)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Constant, ast.JoinedStr)):
                continue
            if isinstance(node, ast.Constant) and not isinstance(node.value, str):
                continue
            if node in docstrings or isinstance(parents.get(node), ast.JoinedStr):
                continue
            text = (
                node.value
                if isinstance(node, ast.Constant)
                else ast.get_source_segment(source, node)
            )
            chain, current = [], node
            while current in parents and len(chain) < 6:
                current = parents[current]
                chain.append(current)
            calls = [c for c in chain if isinstance(c, ast.Call)]
            context = ast.unparse(calls[0].func) if calls else type(parents.get(node)).__name__
            classification = "REVIEW"
            if any(isinstance(c, ast.Raise) for c in chain):
                classification = "TECHNICAL_ERROR_REVIEW_PRESENTATION"
            elif context in ("print", "input", "ok", "warn", "fail") or any(
                isinstance(c, ast.keyword)
                and c.arg in ("help", "description", "title", "label", "message")
                for c in chain
            ):
                classification = "UI_CANDIDATE"
            elif context.startswith(("logger.", "logging.", "log.")):
                classification = "TECHNICAL_LOG"
            add(
                node.lineno,
                node.col_offset + 1,
                "python-fstring" if isinstance(node, ast.JoinedStr) else "python-string",
                text,
                context,
                classification,
            )
    elif path.suffix == ".html":

        class Extract(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.stack = []

            def handle_starttag(self, tag, attrs):
                self.stack.append(tag)
                for key, value in attrs:
                    if value:
                        add(
                            *self.position(),
                            "html-attribute",
                            value,
                            tag + "@" + key,
                            "UI_CANDIDATE"
                            if key in ("title", "placeholder", "aria-label", "alt", "label")
                            else "REVIEW",
                        )

            def handle_startendtag(self, tag, attrs):
                self.handle_starttag(tag, attrs)
                self.stack.pop()

            def handle_endtag(self, tag):
                if tag in self.stack:
                    self.stack = self.stack[: len(self.stack) - 1 - self.stack[::-1].index(tag)]

            def position(self):
                line, col = self.getpos()
                return line, col + 1

            def handle_data(self, data):
                add(
                    *self.position(),
                    "html-text",
                    data,
                    "/".join(self.stack),
                    "REVIEW_EMBEDDED_CODE"
                    if any(t in self.stack for t in ("script", "style"))
                    else "UI_CANDIDATE",
                )

        Extract().feed(source)
    elif path.suffix in (".json", ".info", ".map", ".registry", ".schema", ".lang"):
        document = json.loads(source)

        def walk(value, trail):
            if isinstance(value, dict):
                for key, child in value.items():
                    walk(child, [*trail, key])
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, [*trail, str(index)])
            elif isinstance(value, str):
                literal = json.dumps(value, ensure_ascii=False)
                offset = source.find(literal)
                if offset < 0:
                    offset = source.find(json.dumps(value, ensure_ascii=True))
                line = source.count("\n", 0, max(offset, 0)) + 1
                classification = (
                    "CATALOG" if path.suffix == ".lang" and "strings" in trail else "REVIEW"
                )
                add(
                    line,
                    1,
                    "json-value",
                    value,
                    ".".join(trail),
                    classification,
                    trail[-1] if classification == "CATALOG" else "",
                )

        walk(document, [])
    else:
        # Conservative lexical scanner: comments skipped; templates retained whole,
        # including interpolation. Regex/template nesting is explicitly not a JS AST.
        pattern = re.compile(
            r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\[\s\S]|[^"\\])*"|\'(?:\\[\s\S]|[^\'\\])*\'|`(?:\\[\s\S]|[^`\\])*`'
        )
        for match in pattern.finditer(source):
            raw = match.group()
            if raw.startswith(("//", "/*")):
                continue
            line = source.count("\n", 0, match.start()) + 1
            col = match.start() - source.rfind("\n", 0, match.start())
            context = source[
                max(source.rfind("\n", 0, match.start()) + 1, match.start() - 100) : match.start()
            ].strip()
            add(
                line,
                col,
                "lexical-template" if raw[0] == "`" else "lexical-string",
                raw[1:-1],
                context,
            )
    return rows


def generate():
    paths = []
    for directory in ("src/lanctl", "gui", "plugins-src", "bundled/languages", "packaging"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and (
                path.suffix
                in (
                    ".py",
                    ".js",
                    ".css",
                    ".html",
                    ".lang",
                    ".info",
                    ".map",
                    ".registry",
                    ".schema",
                    ".iss",
                    ".lua",
                    ".sh",
                    ".ps1",
                )
                or path.name in ("main.exec", "catalog.json")
            ):
                paths.append(path)
    rows, files = [], []
    for path in paths:
        items = collect(path)
        rows.extend(items)
        files.append(
            {
                "file": str(path.relative_to(ROOT)),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "launcher": scope(path.relative_to(ROOT))[0],
                "interface": scope(path.relative_to(ROOT))[1],
                "entries": len(items),
            }
        )
    rows.sort(key=lambda r: (r["file"], r["line"], r["column"], r["kind"]))
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    counts = Counter((r["launcher"], r["interface"]) for r in rows)
    report = "# P100 — Inventario estático de cadenas\n\n"
    report += "Generado con `python3 tools/generate_string_inventory.py`. No importa ni ejecuta LANCTL.\n\n"
    report += f"Archivos examinados: **{len(files)}**. Entradas: **{len(rows)}**. "
    report += f"Valores de texto distintos: **{len(set(r['text'] for r in rows))}**.\n\n"
    report += "Son ocurrencias conservadoras de literales, no un recuento de traducciones necesarias ni una certificación de cobertura funcional.\n\n"
    report += "| Propietario | Interfaz de origen | Ocurrencias |\n|---|---|---:|\n"
    for (launcher, interface), count in sorted(counts.items()):
        report += f"| {launcher} | {interface} | {count} |\n"
    report += "\n## Clasificación inicial\n\n| Clase | Ocurrencias |\n|---|---:|\n"
    for category, count in sorted(Counter(r["classification"] for r in rows).items()):
        report += f"| {category} | {count} |\n"
    report += "\nLas clases son indicios automáticos: `UI_CANDIDATE` también puede contener datos técnicos; "
    report += "`REVIEW` conserva valores sin decidir su destino; los errores requieren revisar cómo llegan a pantalla. "
    report += "`KEY_REFERENCE` identifica referencias, no traducciones. La propiedad SHARED no duplica entradas entre consumidores.\n"
    return {
        "docs/P100-STRING-INVENTORY.csv": stream.getvalue(),
        "docs/P100-STRING-FILES.json": json.dumps(files, ensure_ascii=False, indent=2) + "\n",
        "docs/P100-STRING-SUMMARY.md": report,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for name, content in generate().items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != content.encode():
                raise SystemExit(f"Inventory out of date: {name}")
        else:
            path.write_bytes(content.encode())
    print("P100 inventory: current" if args.check else "P100 inventory: generated")


if __name__ == "__main__":
    main()
