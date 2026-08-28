from __future__ import annotations

import getpass
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

SecretReader = Callable[[str], str]
_SECRET_READER: ContextVar[SecretReader | None] = ContextVar("lanctl_secret_reader", default=None)


def read_secret(prompt: str) -> str:
    """Lee un secreto usando el frontend activo o la consola convencional."""

    reader = _SECRET_READER.get()
    return reader(prompt) if reader else getpass.getpass(prompt)


@contextmanager
def use_secret_reader(reader: SecretReader) -> Iterator[None]:
    """Permite que una interfaz interactiva controle dónde solicita secretos."""

    token = _SECRET_READER.set(reader)
    try:
        yield
    finally:
        _SECRET_READER.reset(token)
