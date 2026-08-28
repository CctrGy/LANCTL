"""Modelo y validación de identificadores físicos IDF."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class IDFSize(str, Enum):
    SHORT = "short"
    LONG = "long"


_PATTERNS = {
    IDFSize.SHORT: re.compile(r"^[A-Z]{2}-[0-9]{2}$"),
    IDFSize.LONG: re.compile(r"^[A-Z]{4}-[0-9]{4}$"),
}
_WIDTHS = {IDFSize.SHORT: (2, 2, 99), IDFSize.LONG: (4, 4, 9999)}


@dataclass(frozen=True, order=True)
class IDF:
    """Un identificador corto ``AB-12`` o largo ``ABCD-1234``."""

    prefix: str
    number: int
    size: IDFSize

    def __post_init__(self) -> None:
        prefix_width, _, maximum = _WIDTHS[self.size]
        normalized = self.prefix.strip().upper()
        if len(normalized) != prefix_width or not normalized.isascii() or not normalized.isalpha():
            raise ValueError(
                f"el prefijo {self.size.value} debe contener {prefix_width} letras ASCII"
            )
        if isinstance(self.number, bool) or not isinstance(self.number, int):
            raise TypeError("el número IDF debe ser un entero")
        if not 0 <= self.number <= maximum:
            raise ValueError(f"el número IDF debe estar entre 0 y {maximum}")
        object.__setattr__(self, "prefix", normalized)

    @classmethod
    def build(cls, prefix: str, number: int, size: IDFSize | str | None = None) -> IDF:
        normalized = prefix.strip().upper()
        resolved_size = (
            IDFSize(size)
            if size is not None
            else {2: IDFSize.SHORT, 4: IDFSize.LONG}.get(len(normalized))
        )
        if resolved_size is None:
            raise ValueError("el prefijo IDF debe tener 2 o 4 letras")
        return cls(normalized, number, resolved_size)

    @classmethod
    def parse(cls, value: str) -> IDF:
        normalized = value.strip().upper()
        for size, pattern in _PATTERNS.items():
            if pattern.fullmatch(normalized):
                prefix, number = normalized.split("-", 1)
                return cls(prefix, int(number), size)
        raise ValueError("IDF no válido; se esperaba AB-12 o ABCD-1234")

    @classmethod
    def is_valid(cls, value: str) -> bool:
        try:
            cls.parse(value)
        except (TypeError, ValueError):
            return False
        return True

    @property
    def value(self) -> str:
        _, number_width, _ = _WIDTHS[self.size]
        return f"{self.prefix}-{self.number:0{number_width}d}"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"IDF({self.value!r})"
