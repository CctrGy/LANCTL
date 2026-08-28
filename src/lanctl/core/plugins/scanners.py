from __future__ import annotations

import ipaddress
from collections.abc import Iterable


def run_scanner_extensions(methods: Iterable[str], timeout: float) -> dict[str, set[str]]:
    """Ejecuta extensiones scanner activas y normaliza sus resultados."""
    from lanctl.core.plugins import get_plugin_manager

    requested = {str(method).strip().casefold() for method in methods}
    findings: dict[str, set[str]] = {}
    manager = get_plugin_manager()
    for extension in manager.extensions.list("scanner"):
        specification = extension.specification
        supported = {str(method).strip().casefold() for method in specification.get("methods", [])}
        selected = sorted(requested & supported)
        function_id = str(specification.get("function", "")).strip()
        if not selected or not function_id:
            continue
        try:
            result = manager.functions.call(function_id, selected, float(timeout), caller="LANCTL")
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.Plugin.Scanner.Execution",
                code="PLUGIN.SCANNER.EXECUTION_FAILED",
                level=47,
                details={"extensionId": extension.extension_id},
                print_output=False,
            )
            manager.audit(
                extension.owner,
                "SCANNER",
                extension.extension_id,
                "ERROR",
                str(error),
            )
            continue
        if not result.success or not isinstance(result.data, dict):
            from lanctl.core.errors import errors

            errors.emit(
                origin="LANCTL.Plugin.Scanner.Result",
                code="PLUGIN.SCANNER.INVALID_RESULT",
                level=37 if not result.success else 48,
                message=result.message or "El scanner devolvió datos incompatibles",
                details={"extensionId": extension.extension_id},
                print_output=False,
            )
            continue
        for raw_ip, raw_methods in result.data.items():
            try:
                ip = str(ipaddress.IPv4Address(str(raw_ip)))
            except ipaddress.AddressValueError:
                continue
            normalized = {
                str(method).strip().upper()
                for method in raw_methods
                if str(method).strip().casefold() in supported
            }
            if normalized:
                findings.setdefault(ip, set()).update(normalized)
    return findings
