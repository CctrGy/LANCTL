from __future__ import annotations


def resolve_manufacturer_extensions(mac: str, manager=None) -> str:
    """Consulta adaptadores de fabricante activos y aísla sus errores."""
    if manager is None:
        from app.plugins import get_plugin_manager

        manager = get_plugin_manager()
    for extension in manager.extensions.list("device-adapter"):
        specification = extension.specification
        if str(specification.get("role", "")).casefold() != "manufacturer-resolver":
            continue
        function_id = str(specification.get("function", "")).strip()
        if not function_id:
            continue
        try:
            result = manager.functions.call(function_id, mac, caller="LANCTL")
        except (OSError, RuntimeError, TypeError, ValueError) as error:
            manager.audit(
                extension.owner,
                "DEVICE ADAPTER",
                extension.extension_id,
                "ERROR",
                str(error),
            )
            continue
        if result.success and isinstance(result.data, str) and result.data.strip():
            return result.data.strip()
    return ""
