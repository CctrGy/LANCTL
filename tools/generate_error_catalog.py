from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from lanctl.core.errors import make_error_id  # noqa: E402

OUTPUT = ROOT / "errorList.txt"


def stable_ast_dump(node: ast.AST) -> str:
    """Preserve Python 3.10-3.12 signatures when newer AST dumps omit empty lists."""
    options = {"annotate_fields": False, "include_attributes": False}
    if sys.version_info >= (3, 13):
        options["show_empty"] = True
    return ast.dump(node, **options)


@dataclass(frozen=True)
class Point:
    path: str
    line: int
    origin: str
    kind: str
    signature: str
    level: int


def text(node: ast.AST | None) -> str:
    if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant):
        return str(node.args[0].value).casefold()
    return ""


def classify(kind: str, node: ast.AST, path: str) -> int:
    logical_path = path
    prefixes = {
        "src/lanctl/apps/ip/interfaces/cli/commands/": "src/commands/",
        "src/lanctl/apps/ip/infrastructure/services/": "src/services/",
        "src/lanctl/apps/ip/domain/models/": "src/models/",
        "src/lanctl/apps/ip/infrastructure/protocols/": "src/protocols/",
        "src/lanctl/apps/access/": "src/access/",
        "src/lanctl/apps/monitor/": "src/monitor/",
        "src/lanctl/core/plugins/": "src/plugins/",
        "src/lanctl/core/projects/": "src/projects/",
        "src/lanctl/core/": "src/core/",
        "src/lanctl/shared/assets/": "src/assets/",
    }
    for current, legacy in prefixes.items():
        if path.startswith(current):
            logical_path = legacy + path.removeprefix(current)
            break
    path = logical_path
    message = text(node.exc if isinstance(node, ast.Raise) else node)
    exc = ""
    if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
        exc = getattr(node.exc.func, "id", "")
    if kind == "diagnostic":
        for kw in getattr(node, "keywords", []):
            if kw.arg == "level" and isinstance(kw.value, ast.Constant):
                return int(kw.value.value) if isinstance(kw.value.value, int) else 42
        return 42
    if kind in {"exit", "return-error", "print-error"}:
        if any(x in message for x in ("timeout", "conex", "red")):
            return 46
        if kind == "print-error":
            return 34
        if path.startswith("src/access/"):
            return 46
        return 41
    if exc == "PermissionError":
        return (
            44 if any(x in message for x in ("autentic", "credencial", "sesion", "clave")) else 45
        )
    if exc in {"ConnectionError", "TimeoutError"}:
        return 46
    if exc in {"OSError", "FileNotFoundError"}:
        return (
            43 if any(x in message for x in ("archivo", "almac", "directorio", "bloqueo")) else 46
        )
    if exc == "RuntimeError":
        if "plugin" in path:
            return 47
        if any(x in message for x in ("dependencia", "requiere", "disponible", "soportad")):
            return 42
        return 49 if any(x in message for x in ("intern", "invariante", "adquirido")) else 41
    if any(x in message for x in ("corrupt", "checksum", "firma", "json", "xml")):
        return 48
    if any(x in message for x in ("ya existe", "duplicad", "colision", "ambigua", "coincide")):
        return 34
    if any(x in message for x in ("config", "perfil", "formato", "rango", "version")):
        return 33
    if any(x in message for x in ("no existe", "no encontr", "no disponible", "falta")):
        return 32
    if any(x in message for x in ("mac", "identidad", "huella")):
        return 35
    if any(x in message for x in ("confirm", "--yes", "cancelad")):
        return 39
    if any(x in message for x in ("acción no", "accion no", "no soportad", "no ofrece")):
        return 42
    if "indica" in message:
        return 32
    if any(
        x in message
        for x in ("debe ", "debe estar", "entre ", "fuera de", "mayor que", "menor que")
    ):
        return 33
    if path.startswith("src/commands/") or any(
        x in message for x in ("usa:", "argumento", "valor", "puerto")
    ):
        return 31
    if isinstance(node, ast.Raise) and node.exc is None:
        if path.startswith("src/plugins/"):
            return 47
        if path.startswith("src/access/"):
            return 46
        if path.startswith(("src/monitor/", "src/projects/")):
            return 43
        if path.startswith("src/protocols/"):
            return 42
        return 49
    if path.startswith("src/plugins/"):
        return (
            48
            if any(
                x in path for x in ("models.py", "contracts.py", "package.py", "ui_contracts.py")
            )
            else 47
        )
    if path.startswith("src/core/"):
        if any(
            x in path
            for x in ("database", "history", "config", "credentials", "file_transaction", "tasking")
        ):
            return 43
        if any(x in path for x in ("parser", "query", "conditions")):
            return 33
        if "errors.py" in path:
            return 49
        return 42
    if path.startswith("src/monitor/"):
        return 43 if any(x in path for x in ("database", "scheduler", "sessions")) else 42
    if path.startswith("src/projects/"):
        return 43
    if path.startswith(("src/assets/", "src/models/")) or path in {
        "src/i18n.py",
        "src/gui_theme.py",
    }:
        return 33
    if path.startswith("src/protocols/"):
        return 42
    if path.startswith("src/services/"):
        return 37
    return 36


def call_name(node: ast.Call) -> str:
    parts, current = [], node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def return_is_error(node: ast.Return) -> bool:
    value = node.value
    if isinstance(value, ast.Constant) and isinstance(value.value, int):
        return not isinstance(value.value, bool) and value.value >= 2
    if isinstance(value, (ast.Tuple, ast.List)) and value.elts:
        first = value.elts[0]
        return isinstance(first, ast.Constant) and isinstance(first.value, int) and first.value >= 2
    if isinstance(value, ast.Dict):
        pairs = {
            str(k.value).casefold(): v
            for k, v in zip(value.keys, value.values)
            if isinstance(k, ast.Constant)
        }
        if isinstance(pairs.get("ok"), ast.Constant) and pairs["ok"].value is False:
            return True
        status = pairs.get("status")
        return isinstance(status, ast.Constant) and str(status.value).casefold() in {
            "error",
            "failed",
            "failure",
        }
    return False


class Collector(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path, self.scope, self.points, self.occurrences = path, [], [], {}

    def _add(self, node: ast.AST, kind: str, signature: str) -> None:
        # Relocation must not rename the published identities of monitor errors.
        identity_path = {
            "src/lanctl/apps/monitor/commands.py": "src/lanctl/apps/ip/interfaces/cli/commands/monitor.py",
        }.get(self.path, self.path)
        module = identity_path.removesuffix(".py").replace("/", ".")
        origin = ".".join([module, *self.scope]) if self.scope else module
        occurrence_key = (origin, kind, signature)
        ordinal = self.occurrences.get(occurrence_key, 0) + 1
        self.occurrences[occurrence_key] = ordinal
        signature = f"{signature}#{ordinal}"
        self.points.append(
            Point(self.path, node.lineno, origin, kind, signature, classify(kind, node, self.path))
        )

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node):
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Raise(self, node):
        signature = stable_ast_dump(node.exc) if node.exc is not None else "reraised-exception"
        self._add(node, "raise", signature)
        self.generic_visit(node)

    def visit_Call(self, node):
        name = call_name(node)
        if name in {"sys.exit", "exit", "quit"} or name.endswith(".exit"):
            self._add(node, "exit", stable_ast_dump(node))
        elif name.endswith(("errors.emit", "errors.from_exception")):
            self._add(node, "diagnostic", stable_ast_dump(node))
        elif name.endswith("print_error"):
            self._add(node, "print-error", stable_ast_dump(node))
        self.generic_visit(node)

    def visit_Return(self, node):
        if return_is_error(node):
            self._add(
                node,
                "return-error",
                stable_ast_dump(node.value),
            )
        self.generic_visit(node)


def render_catalog() -> tuple[str, int]:
    points = []
    runtime_events: list[tuple[str, int, str, int, str, str]] = []
    for path in sorted((ROOT / "src" / "lanctl").rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        collector = Collector(relative)
        collector.visit(tree)
        points.extend(collector.points)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not call_name(node).endswith(("errors.emit", "errors.from_exception")):
                continue
            arguments = {keyword.arg: keyword.value for keyword in node.keywords}
            origin = arguments.get("origin")
            code = arguments.get("code")
            if not (
                isinstance(origin, ast.Constant)
                and isinstance(origin.value, str)
                and isinstance(code, ast.Constant)
                and isinstance(code.value, str)
            ):
                continue
            level = arguments.get("level")
            severity = (
                level.value
                if isinstance(level, ast.Constant) and isinstance(level.value, int)
                else 42
            )
            runtime_events.append(
                (
                    make_error_id(origin.value, code.value),
                    severity,
                    relative,
                    node.lineno,
                    origin.value,
                    "diagnostic",
                )
            )
    rows, identifiers = [], set()
    for point in points:
        key = f"{point.origin}.{point.kind}"
        identifier = make_error_id(key, point.signature)
        if identifier in identifiers:
            raise RuntimeError(f"colisión de identificador: {identifier}")
        identifiers.add(identifier)
        rows.append((identifier, point.level, point.path, point.line, point.origin, point.kind))
    for row in runtime_events:
        if row[0] not in identifiers:
            identifiers.add(row[0])
            rows.append(row)
    lines = [
        "# LANCTL error catalog - generated; do not edit manually",
        "# FORMAT: ERROR_ID | LEVEL | SOURCE_FILE | LINE | ORIGIN | KIND",
        "# Static IDs derive from semantic points; literal runtime events use origin + code",
    ]
    lines.extend(
        f"{i} | {level:02d} | {path} | {line} | {origin} | {kind}"
        for i, level, path, line, origin, kind in sorted(rows)
    )
    return "\n".join(lines) + "\n", len(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera o valida el catálogo de errores.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="No escribe; falla si errorList.txt no coincide con el código fuente.",
    )
    args = parser.parse_args(argv)
    content, count = render_catalog()
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_text(encoding="utf-8") != content:
            print(f"{OUTPUT} está desactualizado; ejecuta {Path(__file__).name}", file=sys.stderr)
            return 1
        print(f"{OUTPUT}: actualizado ({count} puntos catalogados)")
        return 0
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"{OUTPUT}: {count} puntos catalogados")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
