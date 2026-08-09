from __future__ import annotations

from collections.abc import Callable
from dataclasses import is_dataclass

from app.plugins.contracts import FunctionResult


class FunctionRegistry:
    """Funciones públicas tipadas registradas por core y complementos."""

    def __init__(self, audit=None) -> None:
        self._items: dict[str, tuple[str, Callable, type]] = {}
        self.audit = audit or (lambda *args, **kwargs: None)

    def register(
        self,
        function_id: str,
        handler: Callable,
        return_contract: type = FunctionResult,
        *,
        owner: str,
    ) -> None:
        key = function_id.casefold()
        if key in self._items:
            raise ValueError(f"función ya registrada: {function_id}")
        if not callable(handler) or not is_dataclass(return_contract):
            raise TypeError("handler y contrato de retorno no válidos")
        self._items[key] = (owner, handler, return_contract)

    def call(self, function_id: str, *args, caller: str = "LANCTL", **kwargs):
        try:
            owner, handler, contract = self._items[function_id.casefold()]
        except KeyError as error:
            raise ValueError(f"función no registrada: {function_id}") from error
        try:
            result = handler(*args, **kwargs)
            if not isinstance(result, contract):
                raise TypeError(f"{function_id} debe devolver {contract.__name__}")
            self.audit(caller, "FUNCTION CALL", function_id, "OK", f"owner={owner}")
            return result
        except Exception as error:
            self.audit(caller, "FUNCTION CALL", function_id, "ERROR", str(error))
            raise

    def owner(self, function_id: str) -> str:
        try:
            return self._items[function_id.casefold()][0]
        except KeyError as error:
            raise ValueError(f"función no registrada: {function_id}") from error

    def remove_owner(self, owner: str) -> None:
        self._items = {key: value for key, value in self._items.items() if value[0] != owner}
