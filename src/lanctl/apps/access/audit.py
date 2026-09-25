"""Non-secret audit for access management operations."""

from lanctl.core.errors import errors


def completed(operation: str, count: int) -> None:
    from lanctl.core.plugins.manager import get_plugin_manager

    errors.emit(
        level=21,
        origin="LANCTL.Access.Vault.Operation",
        code="ACCESS.VAULT.COMPLETED",
        message=f"{operation}: {count} credenciales",
        print_output=False,
    )
    try:
        get_plugin_manager().events.emit(
            "LANCTL.Access.Vault.Completed", {"operation": operation, "count": count}
        )
    except Exception as exc:  # noqa: BLE001 - optional observer cannot undo a committed operation
        errors.emit(
            level=33,
            origin="LANCTL.Access.Vault.Observer",
            code="ACCESS.VAULT.OBSERVER_FAILED",
            message="operación completada; observador no disponible",
            details={"exceptionType": type(exc).__name__},
            print_output=False,
        )
