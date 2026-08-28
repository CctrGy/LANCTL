from __future__ import annotations


def resolve_manufacturer_extensions(mac: str, manager=None) -> str:
    """Consulta adaptadores de fabricante activos y aísla sus errores."""
    if manager is None:
        from lanctl.core.plugins import get_plugin_manager

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
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.Plugin.DeviceAdapter.Manufacturer",
                code="PLUGIN.DEVICE_ADAPTER.FAILED",
                level=47,
                details={"extensionId": extension.extension_id},
                print_output=False,
            )
            manager.audit(
                extension.owner,
                "DEVICE ADAPTER",
                extension.extension_id,
                "ERROR",
                str(error),
            )
            continue
        if not result.success:
            from lanctl.core.errors import errors

            errors.emit(
                origin="LANCTL.Plugin.DeviceAdapter.Result",
                code="PLUGIN.DEVICE_ADAPTER.RESULT_FAILED",
                level=37,
                message=result.message or "El adaptador no pudo resolver el fabricante",
                details={"extensionId": extension.extension_id},
                print_output=False,
            )
        if result.success and isinstance(result.data, str) and result.data.strip():
            return result.data.strip()
    return ""
