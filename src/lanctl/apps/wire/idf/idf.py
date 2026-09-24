"""Modelo y validación de identificadores físicos IDF."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class IDFSize(str, Enum):
    """Anchuras uniformes conservadas por compatibilidad con la API original."""

    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"
    EXTENDED = "extended"


_PATTERN = re.compile(r"^(?P<prefix>[A-Z]{2,5})-(?P<number>[0-9]{2,5})$")
_SIZE_WIDTHS = {
    IDFSize.SHORT: 2,
    IDFSize.MEDIUM: 3,
    IDFSize.LONG: 4,
    IDFSize.EXTENDED: 5,
}
_WIDTH_SIZES = {width: size for size, width in _SIZE_WIDTHS.items()}


@dataclass(frozen=True, order=True)
class IDF:
    """Identificador físico con 2-5 letras y 2-5 dígitos.

    Los anchos son independientes: tanto ``ABC-12`` como ``AB-00123`` son
    válidos. Los formatos históricos de dos y cuatro caracteres se conservan.
    """

    prefix: str
    number: int
    prefix_width: int
    number_width: int

    def __post_init__(self) -> None:
        normalized = self.prefix.strip().upper()
        if len(normalized) != self.prefix_width or not normalized.isascii() or not normalized.isalpha():
            raise ValueError("el prefijo IDF debe contener entre 2 y 5 letras ASCII")
        if not 2 <= self.prefix_width <= 5 or not 2 <= self.number_width <= 5:
            raise ValueError("las partes del IDF deben tener entre 2 y 5 caracteres")
        if isinstance(self.number, bool) or not isinstance(self.number, int):
            raise TypeError("el número IDF debe ser un entero")
        if not 0 <= self.number < 10**self.number_width:
            raise ValueError(f"el número IDF debe estar entre 0 y {10**self.number_width - 1}")
        object.__setattr__(self, "prefix", normalized)

    @classmethod
    def build(
        cls,
        prefix: str,
        number: int,
        size: IDFSize | str | None = None,
        *,
        number_width: int | None = None,
    ) -> IDF:
        """Construye un IDF; ``number_width`` permite elegir dígitos independientes."""
        normalized = prefix.strip().upper()
        prefix_width = _SIZE_WIDTHS[IDFSize(size)] if size is not None else len(normalized)
        resolved_number_width = number_width if number_width is not None else prefix_width
        return cls(normalized, number, prefix_width, resolved_number_width)

    @classmethod
    def parse(cls, value: str) -> IDF:
        normalized = value.strip().upper()
        match = _PATTERN.fullmatch(normalized)
        if not match:
            raise ValueError("IDF no válido; se esperaban 2-5 letras, un guion y 2-5 dígitos")
        prefix = match.group("prefix")
        number = match.group("number")
        return cls(prefix, int(number), len(prefix), len(number))

    @classmethod
    def is_valid(cls, value: str) -> bool:
        try:
            cls.parse(value)
        except (TypeError, ValueError):
            return False
        return True

    @property
    def value(self) -> str:
        return f"{self.prefix}-{self.number:0{self.number_width}d}"

    @property
    def size(self) -> IDFSize | None:
        """Tamaño uniforme histórico, o ``None`` cuando los anchos difieren."""
        if self.prefix_width == self.number_width:
            return _WIDTH_SIZES[self.prefix_width]
        return None

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"IDF({self.value!r})"
