"""Explicit, bounded diagnostic selection and redaction, without network access."""

from __future__ import annotations

import ipaddress
import json
import platform
import re
from datetime import datetime, timezone
from itertools import islice
from pathlib import Path

from lanctl import __version__
from lanctl.core.errors import redact_text
from lanctl.core.file_transaction import atomic_write_text

_SECRET_KEY = re.compile(
    r"password|passwd|credential|secret|token|private.?key|api.?key|authorization|cookie|csrf|pairing",
    re.I,
)
_ASSIGNMENT = re.compile(
    r"""(?i)(["']?(?:api[_ -]?key|password|passwd|secret|token|credential|authorization|cookie|csrf|pairing|private[_ -]?key)["']?\s*[:=]\s*)(?:"[^"]*"|'[^']*'|[^\s,;]+)"""
)
_PRIVATE = re.compile(
    r"-----BEGIN [^-\r\n]*PRIVATE KEY-----.*?(?:-----END [^-\r\n]*PRIVATE KEY-----|$)", re.S
)
_USERINFO = re.compile(r"(\w+://)[^\s/@]+(?::[^\s/@]*)?@")
_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|\\\\|(?<![\w:/])/)(?:[^\s\"'<>|,;]+)")
_EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
_MAC = re.compile(r"(?i)\b[0-9a-f]{2}(?:[:-][0-9a-f]{2}){5}\b")
_ADDRESS = re.compile(
    r"(?<![\w.])(?:\d{1,3}(?:\.\d{1,3}){3}|[0-9A-Fa-f:]*:[0-9A-Fa-f:.]+)(?:%[\w-]+)?(?![\w.])"
)
_IDENTITY_KEYS = {
    "username",
    "user",
    "hostname",
    "host",
    "project",
    "projectpath",
    "path",
    "ip",
    "mac",
    "email",
    "name",
    "alias",
}


def _clean_text(value, anonymize):
    text = _PRIVATE.sub("[SECRET]", str(value)[:65536])
    text = redact_text(text)
    text = _ASSIGNMENT.sub(lambda m: m[1] + "[SECRET]", text)
    text = _USERINFO.sub(r"\1[SECRET]@", text)
    text = re.sub(
        r"\b(?:gh[pousr]_[A-Za-z0-9_]{16,}|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{16,})\b",
        "[SECRET]",
        text,
    )
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = "".join(c for c in text if c.isprintable() or c in "\n\t")
    if anonymize:
        text = _EMAIL.sub("[EMAIL]", text)
        text = _MAC.sub("[MAC]", text)

        def address(match):
            try:
                ipaddress.ip_address(match[0])
            except ValueError:
                return match[0]
            return "[IP]"

        text = _ADDRESS.sub(address, text)
        text = _PATH.sub("[PATH]", text)
    return text[:4096]


def _sanitize(value, anonymize=True, key="", depth=0):
    if _SECRET_KEY.search(key):
        return "[SECRET]"
    if anonymize and key.casefold() in _IDENTITY_KEYS:
        return "[PRIVATE]" if value else value
    if depth > 5:
        return "[DEPTH LIMIT]"
    if isinstance(value, dict):
        return {
            _clean_text(k, anonymize): _sanitize(v, anonymize, str(k), depth + 1)
            for k, v in islice(value.items(), 50)
        }
    if isinstance(value, (list, tuple)):
        return [_sanitize(v, anonymize, depth=depth + 1) for v in value[:200]]
    if isinstance(value, str):
        return _clean_text(value, anonymize)
    if value is None or type(value) in (int, float, bool):
        return value
    return "[UNSUPPORTED VALUE]"


def prepare_diagnostic(
    *,
    description="",
    steps="",
    expected="",
    application="lanctl",
    interface="gui",
    errors=(),
    logs=(),
    plugins=(),
    context=None,
    anonymize=True,
) -> dict:
    if type(anonymize) is not bool:
        raise ValueError("anonymize debe ser booleano")
    if any(
        not isinstance(value, str)
        for value in (description, steps, expected, application, interface)
    ):
        raise ValueError("los campos del reporte deben ser texto")
    if not all(isinstance(v, (list, tuple)) for v in (errors, logs, plugins)) or (
        context is not None and not isinstance(context, dict)
    ):
        raise ValueError("evidencia de diagnóstico no válida")
    grouped = {}
    for error in errors[:200]:
        if not isinstance(error, dict):
            raise ValueError("cada error debe ser un objeto")
        clean = _sanitize(
            {
                k: v
                for k, v in error.items()
                if k
                in {
                    "errorId",
                    "code",
                    "origin",
                    "message",
                    "level",
                    "timestamp",
                    "correlationId",
                    "details",
                }
            },
            anonymize,
        )
        key = tuple(str(clean.get(k, "")) for k in ("origin", "code", "errorId", "message"))
        if key in grouped:
            grouped[key]["count"] += 1
        elif len(grouped) < 50:
            grouped[key] = {**clean, "count": 1}
    report = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "version": __version__,
        "system": {
            "os": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
        },
        "application": application,
        "interface": interface,
        "description": description,
        "steps": steps,
        "expected": expected,
        "errors": list(grouped.values()),
        "logs": list(logs[:200]),
        "plugins": [
            {k: v for k, v in p.items() if k in {"id", "version", "state"}}
            for p in plugins[:100]
            if isinstance(p, dict)
        ],
        "context": {
            k: v
            for k, v in (context or {}).items()
            if k in {"session", "task", "project", "revision", "savedRevision"}
        },
        "anonymized": anonymize,
    }
    return _sanitize(report, anonymize)


def _validated(report):
    if (
        not isinstance(report, dict)
        or type(report.get("schemaVersion")) is not int
        or report["schemaVersion"] != 1
    ):
        raise ValueError("versión de diagnóstico no compatible")
    if type(report.get("anonymized", True)) is not bool:
        raise ValueError("anonimización de diagnóstico no válida")
    # Edited drafts are scrubbed again immediately before exporting or building a URL.
    return _sanitize(report, report.get("anonymized", True))


def diagnostic_markdown(report: dict) -> str:
    clean = _validated(report)
    lines = [
        "# LANCTL · Diagnóstico",
        f"Versión: {clean.get('version', '')}",
        f"Aplicación/interfaz: {clean.get('application', '')}/{clean.get('interface', '')}",
        f"Fecha: {clean.get('generatedAt', '')}",
    ]
    for key, title in (
        ("description", "Descripción"),
        ("steps", "Pasos"),
        ("expected", "Resultado esperado"),
    ):
        lines.extend(["", "## " + title, str(clean.get(key, ""))])
    evidence = {k: clean.get(k) for k in ("system", "context", "errors", "plugins", "logs")}
    lines.extend(
        [
            "",
            "## Evidencia seleccionada",
            "````json",
            json.dumps(evidence, ensure_ascii=False, indent=2),
            "````",
        ]
    )
    return "\n".join(lines) + "\n"


def export_diagnostic(report: dict, path) -> str:
    target = Path(path)
    atomic_write_text(target, diagnostic_markdown(report))
    return str(target.resolve())
