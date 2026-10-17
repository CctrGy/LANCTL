"""Human-reviewed GitHub form adapter; the diagnostic core has no GitHub dependency."""

from urllib.parse import urlencode

from lanctl.core.diagnostics import diagnostic_markdown
from lanctl.core.official_links import get_official_links


def bug_report_url(report: dict) -> str:
    body = diagnostic_markdown({**report, "logs": []})
    title = "LANCTL: informe de error"
    base = get_official_links()["github"] + "/issues/new?"
    body += "\nAdjunta el diagnóstico exportado si necesitas incluir los logs seleccionados.\n"
    # Keep URLs useful on Windows and browsers with conservative length limits.
    while len(base + urlencode({"title": title, "body": body})) > 6000:
        body = (
            body[: max(1, len(body) // 2)] + "\n[Resumen abreviado; adjuntar diagnóstico exportado]"
        )
    return base + urlencode({"title": title, "body": body})
