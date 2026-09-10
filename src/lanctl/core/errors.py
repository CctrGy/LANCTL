from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Callable, Mapping
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock, local
from typing import Any

from lanctl.core.logger import write_log


class ErrorLevel:
    """Escala continua; los múltiplos de diez son sólo referencias."""

    MINIMUM = 1
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    MAXIMUM = 59

    @classmethod
    def parse(cls, value: str | int) -> int:
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
                return int(getattr(cls, normalized))
            try:
                value = int(normalized)
            except ValueError as error:
                raise ValueError(f"nivel de error no válido: {value}") from error
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not cls.MINIMUM <= value <= cls.MAXIMUM
        ):
            raise ValueError(f"el nivel de error debe estar entre {cls.MINIMUM} y {cls.MAXIMUM}")
        return value

    @classmethod
    def label(cls, value: int) -> str:
        value = cls.parse(value)
        if value >= cls.CRITICAL:
            return "CRITICAL"
        if value >= cls.ERROR:
            return "ERROR"
        if value >= cls.WARNING:
            return "WARNING"
        if value >= cls.INFO:
            return "INFO"
        return "DEBUG"


_ORIGIN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z][A-Za-z0-9_-]*)+$")
_CODE = re.compile(r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*)*$")
_ERROR_ID = re.compile(r"^0e[0-9A-F]{8}$")
_SECRET_PARTS = (
    "password",
    "passwd",
    "secret",
    "token",
    "credential",
    "private_key",
    "authorization",
    "cookie",
    "csrf",
    "pairing",
)
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|passwd|secret|token|credential|authorization|cookie|csrf|pairing|"
    r"private[_ -]?key)\b(\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)"
)
_BEARER_TOKEN = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")
_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN [^-\r\n]*PRIVATE KEY-----.*?-----END [^-\r\n]*PRIVATE KEY-----",
    re.DOTALL,
)


def redact_text(value: str) -> str:
    """Oculta secretos habituales sin modificar texto que sólo nombra el campo."""
    value = _PRIVATE_KEY_BLOCK.sub("***PRIVATE KEY REDACTED***", str(value))
    value = _BEARER_TOKEN.sub("Bearer ***", value)
    return _SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}{match.group(2)}***", value)


def make_error_id(origin: str, code: str) -> str:
    """Identificador estable del tipo/punto de error, no de cada ocurrencia."""
    source = f"{origin.casefold()}\0{code.upper()}".encode()
    return "0e" + hashlib.blake2s(source, digest_size=4).hexdigest().upper()


def _redact(value: Any, key: str = "") -> Any:
    if any(part in key.casefold() for part in _SECRET_PARTS):
        return "***"
    if isinstance(value, Mapping):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return repr(value)


@dataclass(frozen=True, slots=True)
class ErrorEvent:
    level: str | int
    origin: str
    code: str
    message: str
    recoverable: bool = True
    details: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc).astimezone())
    error_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "level", ErrorLevel.parse(self.level))
        if not _ORIGIN.fullmatch(self.origin):
            raise ValueError(f"origen de error no válido: {self.origin}")
        normalized_code = self.code.strip().upper()
        if not _CODE.fullmatch(normalized_code):
            raise ValueError(f"código de error no válido: {self.code}")
        object.__setattr__(self, "code", normalized_code)
        identifier = self.error_id or make_error_id(self.origin, normalized_code)
        if not _ERROR_ID.fullmatch(identifier):
            raise ValueError("el identificador debe usar el formato 0eXXXXXXXX hexadecimal")
        object.__setattr__(self, "error_id", identifier)
        message = redact_text(str(self.message)).strip() or "Error sin descripción"
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "details", _redact(dict(self.details)))

    @property
    def level_name(self) -> str:
        return ErrorLevel.label(self.level)

    def __str__(self) -> str:
        return f"[{self.level_name}:{self.level} {self.error_id}] {self.message}"

    def terminal_message(self) -> str:
        """Devuelve el resumen humano; el detalle técnico permanece en logs/repr."""
        return f"{self.level_name}: {self.message} ({self.error_id})"

    def __repr__(self) -> str:
        return (
            f"ErrorEvent(id={self.error_id!r}, level={self.level}, "
            f"severity={self.level_name}, origin={self.origin!r}, "
            f"code={self.code!r}, message={self.message!r}, "
            f"recoverable={self.recoverable})"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "errorId": self.error_id,
            "level": self.level,
            "severity": self.level_name,
            "origin": self.origin,
            "code": self.code,
            "message": self.message,
            "recoverable": self.recoverable,
            "details": dict(self.details),
            "correlationId": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }


class LanctlError(Exception):
    def __init__(self, event: ErrorEvent, *, print_output: bool = True, exit_code: int = 2) -> None:
        super().__init__(event.message)
        self.event = event
        self.print_output = bool(print_output)
        self.exit_code = int(exit_code)

    def __repr__(self) -> str:
        return repr(self.event)


class ErrorManager:
    def __init__(
        self,
        *,
        logger: Callable[[str], Any] = write_log,
        output: Callable[[str], Any] | None = None,
        minimum_level: int | None = None,
    ) -> None:
        self._logger = logger
        self._output = output
        self._minimum_level = minimum_level
        self._seen: set[str] = set()
        self._seen_lock = Lock()
        self._threshold_state = local()

    def _log_enabled(self, level: int) -> bool:
        if self._minimum_level is not None:
            minimum = self._minimum_level
        else:
            if getattr(self._threshold_state, "active", False):
                return level >= ErrorLevel.INFO
            self._threshold_state.active = True
            try:
                from lanctl.core.config import load_config

                minimum = int(load_config().get("errorLogLevel", ErrorLevel.INFO))
            except (OSError, TypeError, ValueError):
                minimum = ErrorLevel.INFO
            finally:
                self._threshold_state.active = False
        return level >= max(ErrorLevel.MINIMUM, min(ErrorLevel.MAXIMUM, minimum))

    def emit(
        self,
        *,
        level: str | int = 42,
        origin: str,
        code: str,
        message: str,
        error_id: str | None = None,
        recoverable: bool = True,
        details: Mapping[str, Any] | None = None,
        correlation_id: str | None = None,
        break_execution: bool = False,
        print_output: bool = True,
        exit_code: int = 2,
        once_key: str | None = None,
    ) -> ErrorEvent:
        event = ErrorEvent(
            level,
            origin,
            code,
            message,
            recoverable,
            details or {},
            correlation_id or str(uuid.uuid4()),
            error_id=error_id,
        )
        payload = json.dumps(event.to_dict(), ensure_ascii=False, separators=(",", ":"))
        duplicate = False
        if once_key:
            with self._seen_lock:
                duplicate = once_key in self._seen
                self._seen.add(once_key)
        if self._log_enabled(event.level) and not duplicate:
            with suppress(Exception):
                self._logger("ERROR_EVENT " + payload)
        if break_execution:
            raise LanctlError(event, print_output=print_output, exit_code=exit_code)
        if print_output:
            if self._output is not None:
                self._output(str(event))
            else:
                from lanctl.core.console import error

                error(str(event), log=False)
        return event

    def from_exception(
        self, exception: Exception, *, origin: str, code: str = "CORE.EXCEPTION", **options: Any
    ) -> ErrorEvent:
        if isinstance(exception, LanctlError):
            return exception.event
        details = dict(options.pop("details", {}) or {})
        details.setdefault("exceptionType", type(exception).__name__)
        return self.emit(
            origin=origin,
            code=code,
            message=str(exception) or type(exception).__name__,
            details=details,
            **options,
        )


errors = ErrorManager()
