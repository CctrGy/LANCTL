from __future__ import annotations

import json
from datetime import datetime

import pytest

from lanctl.core.errors import ErrorEvent, ErrorLevel, ErrorManager, LanctlError
from lanctl.core.plugins.api import PluginApi
from lanctl.core.tasking import result


def test_error_event_validates_and_redacts_sensitive_details():
    event = ErrorEvent(
        "warning",
        "LANCTL.Network.Scanner",
        "network.scan.failed",
        "No se pudo completar",
        details={"host": "192.0.2.1", "password": "visible", "nested": {"token": "x"}},
    )

    assert event.level == ErrorLevel.WARNING
    assert event.code == "NETWORK.SCAN.FAILED"
    assert event.details["password"] == "***"
    assert event.details["nested"]["token"] == "***"
    assert "visible" not in repr(event)


def test_error_event_redacts_secrets_embedded_in_messages_and_values():
    private_key = "-----BEGIN PRIVATE KEY-----\nvisible-key\n-----END PRIVATE KEY-----"
    event = ErrorEvent(
        41,
        "LANCTL.Security.Redaction",
        "SECURITY.REDACTION.TEST",
        "password=visible token:abc Authorization=BearerValue Bearer bearer-secret",
        details={"context": f"cookie=session-secret {private_key}"},
    )

    serialized = json.dumps(event.to_dict())
    for secret in (
        "visible",
        "abc",
        "BearerValue",
        "bearer-secret",
        "session-secret",
        "visible-key",
    ):
        assert secret not in serialized
    assert "***" in event.message


def test_error_manager_logs_json_and_can_print_without_breaking():
    logged, printed = [], []
    manager = ErrorManager(logger=logged.append, output=printed.append, minimum_level=1)

    event = manager.emit(
        origin="LANCTL.Core.Test",
        code="CORE.TEST.WARNING",
        message="aviso",
        level="WARNING",
        break_execution=False,
        print_output=True,
    )

    assert printed[0].startswith("[WARNING:30 0e")
    assert logged[0].startswith("ERROR_EVENT ")
    assert json.loads(logged[0].split(" ", 1)[1])["correlationId"] == event.correlation_id
    assert len(event.error_id) == 10


def test_breaking_error_is_rendered_through_repr_at_boundary():
    manager = ErrorManager(logger=lambda _line: None, output=lambda _line: None)

    with pytest.raises(LanctlError) as raised:
        manager.emit(
            origin="LANCTL.Core.Test",
            code="CORE.TEST.FATAL",
            message="detener",
            level=53,
            recoverable=False,
            break_execution=True,
            print_output=True,
            exit_code=7,
        )

    assert raised.value.exit_code == 7
    assert "origin='LANCTL.Core.Test'" in repr(raised.value)
    assert "code='CORE.TEST.FATAL'" in repr(raised.value)
    assert "level=53" in repr(raised.value)


@pytest.mark.parametrize("level", [0, 60, True, "UNKNOWN"])
def test_level_must_be_inside_the_continuous_scale(level):
    with pytest.raises(ValueError):
        ErrorEvent(level, "LANCTL.Core.Test", "CORE.TEST.LEVEL", "error")


def test_error_identifier_is_stable_for_origin_and_code():
    first = ErrorEvent(37, "LANCTL.Core.Test", "CORE.TEST.STABLE", "uno")
    second = ErrorEvent(37, "LANCTL.Core.Test", "CORE.TEST.STABLE", "dos")
    assert first.error_id == second.error_id
    assert first.level_name == "WARNING"


def test_terminal_message_is_compact_but_repr_keeps_diagnostics():
    event = ErrorEvent(
        34,
        "LANCTL.Core.CLI.Command",
        "CLI.VALUEERROR",
        "el grupo ASSETS ya existe",
        error_id="0e0EE4769B",
    )

    assert event.terminal_message() == "WARNING: el grupo ASSETS ya existe (0e0EE4769B)"
    assert "origin='LANCTL.Core.CLI.Command'" in repr(event)


def test_low_level_event_only_reaches_log_when_threshold_allows_it():
    hidden, visible = [], []
    ErrorManager(logger=hidden.append, minimum_level=20).emit(
        level=14,
        origin="LANCTL.Core.Fallback",
        code="CORE.FALLBACK.USED",
        message="fallback",
        print_output=False,
    )
    ErrorManager(logger=visible.append, minimum_level=10).emit(
        level=14,
        origin="LANCTL.Core.Fallback",
        code="CORE.FALLBACK.USED",
        message="fallback",
        print_output=False,
    )
    assert hidden == []
    assert len(visible) == 1


def test_once_key_deduplicates_log_entries():
    logged = []
    manager = ErrorManager(logger=logged.append, minimum_level=1)
    for _ in range(3):
        manager.emit(
            level=6,
            origin="LANCTL.Core.Trace",
            code="CORE.TRACE.ONCE",
            message="detalle",
            print_output=False,
            once_key="same-point",
        )
    assert len(logged) == 1


def test_from_exception_preserves_type_as_safe_context():
    manager = ErrorManager(logger=lambda _line: None, output=lambda _line: None)
    event = manager.from_exception(
        ValueError("dato inválido"),
        origin="LANCTL.Core.Parser",
        code="CORE.PARSER.INVALID",
        print_output=False,
    )
    assert event.details["exceptionType"] == "ValueError"


def test_plugin_error_origin_is_confined_and_exception_is_interpolated(monkeypatch):
    import lanctl.core.errors as error_module

    manager = ErrorManager(logger=lambda _line: None, output=lambda _line: None)
    monkeypatch.setattr(error_module, "errors", manager)
    api = PluginApi("demo-plugin", set(), object())

    event = api.errors.interpolate(
        ValueError("fallo externo"),
        origin="Discovery.SSDP",
        code="PLUGIN.DISCOVERY.FAILED",
        print_output=False,
    )
    assert event.origin == "Plugin.demo-plugin.Discovery.SSDP"
    assert event.details["exceptionType"] == "ValueError"

    with pytest.raises(PermissionError):
        api.errors.emit("PLUGIN.FAIL", "fallo", origin="LANCTL.Core.Spoof")


def test_operation_result_carries_the_same_structured_error():
    event = ErrorEvent("ERROR", "LANCTL.Tasks.Runner", "TASK.FAILED", "falló")
    operation = result(
        "scan",
        "LANCTL.Tasks.Scan",
        "192.0.2.1",
        "error",
        datetime.now().astimezone(),
        error_event=event,
    )
    assert operation.error["correlationId"] == event.correlation_id
    assert operation.error["origin"] == "LANCTL.Tasks.Runner"


@pytest.mark.parametrize("origin", ["LANCTL", ".LANCTL.Core", "LANCTL..Core"])
def test_invalid_origin_is_rejected(origin):
    with pytest.raises(ValueError):
        ErrorEvent("ERROR", origin, "CORE.TEST.ERROR", "error")
