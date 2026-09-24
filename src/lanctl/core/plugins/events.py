from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from threading import RLock

from lanctl.core.errors import LanctlError, errors
from lanctl.core.plugins.contracts import EventContract, EventMetadata, construct_contract
from lanctl.core.plugins.models import EVENT_ID


@dataclass(frozen=True, slots=True)
class HookDecision:
    allowed: bool = True
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class EventDefinition:
    event_id: str
    version: int
    contract: type[EventContract]
    owner: str
    cancelable: bool = False


class EventRegistry:
    def __init__(self) -> None:
        self._definitions: dict[tuple[str, int], EventDefinition] = {}

    def register(
        self,
        event_id: str,
        contract: type[EventContract],
        *,
        owner: str,
        version: int = 1,
        cancelable: bool = False,
    ) -> None:
        if not EVENT_ID.fullmatch(event_id):
            raise ValueError(f"identificador de evento no válido: {event_id}")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise ValueError("la versión del evento debe ser un entero mayor o igual que 1")
        if event_id.startswith("LANCTL.") and owner != "LANCTL":
            raise PermissionError("los plugins no pueden registrar eventos en el namespace LANCTL")
        key = (event_id.casefold(), version)
        if key in self._definitions:
            raise ValueError(f"evento ya registrado: {event_id}@{version}")
        self._definitions[key] = EventDefinition(event_id, version, contract, owner, cancelable)

    def get(self, event_id: str, version: int = 1) -> EventDefinition:
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise ValueError("la versión del evento debe ser un entero mayor o igual que 1")
        try:
            return self._definitions[(event_id.casefold(), version)]
        except KeyError as error:
            raise ValueError(f"evento no registrado: {event_id}@{version}") from error

    def remove_owner(self, owner: str) -> None:
        if owner == "LANCTL":
            raise PermissionError("no se puede retirar el registro de eventos del core")
        self._definitions = {
            key: value for key, value in self._definitions.items() if value.owner != owner
        }


class EventBus:
    def __init__(self, registry: EventRegistry, audit: Callable[..., None] | None = None) -> None:
        self.registry = registry
        self.audit = audit or (lambda *args, **kwargs: None)
        self._subscriptions: dict[tuple[str, int], list[tuple[int, str, Callable]]] = {}
        self._lock = RLock()

    def subscribe(
        self,
        event_id: str,
        handler: Callable,
        *,
        plugin_id: str,
        version: int = 1,
        priority: int = 100,
    ) -> None:
        self.registry.get(event_id, version)
        with self._lock:
            target = self._subscriptions.setdefault((event_id.casefold(), version), [])
            target.append((priority, plugin_id, handler))
            target.sort(key=lambda item: item[0])

    def unsubscribe_plugin(self, plugin_id: str) -> None:
        with self._lock:
            for key in tuple(self._subscriptions):
                self._subscriptions[key] = [
                    v for v in self._subscriptions[key] if v[1] != plugin_id
                ]

    def emit(
        self,
        event_id: str,
        values: dict,
        *,
        source: str = "LANCTL",
        version: int = 1,
        correlation_id: str | None = None,
    ):
        definition = self.registry.get(event_id, version)
        if source != "LANCTL" and source.casefold() != definition.owner.casefold():
            raise PermissionError("el emisor no es propietario del contrato de evento")
        metadata = EventMetadata(
            event_id,
            version,
            source,
            datetime.now().astimezone(),
            correlation_id or str(uuid.uuid4()),
        )
        event = construct_contract(definition.contract, {"metadata": metadata, **values})
        decisions: list[HookDecision] = []
        for _, plugin_id, handler in tuple(
            self._subscriptions.get((event_id.casefold(), version), [])
        ):
            try:
                result = handler(event)
                if isinstance(result, HookDecision):
                    decisions.append(result)
                self.audit(plugin_id, "EVENT HANDLE", event_id, "OK")
            except LanctlError as error:
                # Un break solicitado por un plugin detiene su tarea, no el bus/core.
                self.audit(plugin_id, "EVENT HANDLE", event_id, "ERROR", repr(error))
            except Exception as error:  # noqa: BLE001 - aislamiento de plugins
                event_error = errors.from_exception(
                    error,
                    origin=f"Plugin.{plugin_id}.Events.Handle",
                    code="PLUGIN.EVENT.HANDLER_FAILED",
                    level=45,
                    recoverable=True,
                    break_execution=False,
                    print_output=False,
                    details={"eventId": event_id, "version": version},
                    correlation_id=metadata.correlation_id,
                )
                self.audit(plugin_id, "EVENT HANDLE", event_id, "ERROR", repr(event_error))
        if definition.cancelable:
            denied = next((item for item in decisions if not item.allowed), None)
            return event, denied or HookDecision()
        return event
