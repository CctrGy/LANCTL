"""Errores estructurados y reutilizables de LANWRE."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any


class ErrorLevel(IntEnum):
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class Error(Exception):
    """Excepción estructurada compatible con la antigua clase ``Error``."""

    def __init__(
        self,
        level: int | ErrorLevel,
        caused: str,
        text: str,
        breakable: bool = False,
        *,
        code: str = "LANWRE_ERROR",
        context: Mapping[str, Any] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        if isinstance(level, bool) or not isinstance(level, int):
            raise TypeError("level debe ser un entero o ErrorLevel")
        if not isinstance(caused, str) or not caused.strip():
            raise ValueError("caused debe identificar el origen del error")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text no puede estar vacío")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("code no puede estar vacío")
        if cause is not None and not isinstance(cause, BaseException):
            raise TypeError("cause debe ser una excepción de Python")

        self.level = int(level)
        self.caused = caused.strip()
        self.text = text.strip()
        self.breakable = bool(breakable)
        self.br = self.breakable
        self.code = code.strip().upper()
        self.context = deepcopy(dict(context or {}))
        self.cause = cause
        self.created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        super().__init__(self.text)

    @property
    def level_name(self) -> str:
        try:
            return ErrorLevel(self.level).name
        except ValueError:
            return str(self.level)

    def to_dict(self) -> dict[str, Any]:
        """Devuelve una representación apta para JSON y logs."""
        result: dict[str, Any] = {
            "code": self.code,
            "level": self.level,
            "level_name": self.level_name,
            "caused": self.caused,
            "text": self.text,
            "breakable": self.breakable,
            "context": deepcopy(self.context),
            "created_at": self.created_at,
        }
        if self.cause is not None:
            result["cause"] = {"type": type(self.cause).__name__, "text": str(self.cause)}
        return result

    def write_log(self, directory: str | Path | None = None) -> Path:
        """Registra este error mediante el sistema central de logs.

        La importación local evita una dependencia circular entre las dos
        librerías y permite seguir utilizando ``Error`` de forma independiente.
        """
        from .log import write_error

        return write_error(self, directory)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> Error:
        """Reconstruye un error serializado, salvo su excepción original."""
        error = cls(
            int(value["level"]),
            str(value["caused"]),
            str(value["text"]),
            bool(value.get("breakable", False)),
            code=str(value.get("code", "LANWRE_ERROR")),
            context=value.get("context") or {},
        )
        if "created_at" in value:
            error.created_at = str(value["created_at"])
        return error

    @classmethod
    def wrap(
        cls,
        cause: BaseException,
        *,
        caused: str,
        text: str | None = None,
        level: int | ErrorLevel = ErrorLevel.ERROR,
        breakable: bool = False,
        code: str = "LANWRE_ERROR",
        context: Mapping[str, Any] | None = None,
    ) -> Error:
        """Convierte una excepción cualquiera en un error uniforme."""
        return cls(
            level,
            caused,
            text or str(cause) or type(cause).__name__,
            breakable,
            code=code,
            context=context,
            cause=cause,
        )

    def __str__(self) -> str:
        return f"[{self.code}] {self.caused}: {self.text}"

    def __repr__(self) -> str:
        return (
            f"Error(level={self.level!r}, caused={self.caused!r}, "
            f"text={self.text!r}, breakable={self.breakable!r}, code={self.code!r})"
        )


__all__ = ["Error", "ErrorLevel"]
