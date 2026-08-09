from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar
from weakref import WeakValueDictionary

T = TypeVar("T")

# Las rutas de proyectos y plugins pueden variar durante un proceso largo. Una
# tabla débil conserva cada `RLock` mientras está en uso, sin acumular para
# siempre una entrada por cada archivo procesado por LANCTL.
_THREAD_LOCKS: WeakValueDictionary[str, threading.RLock] = WeakValueDictionary()
_THREAD_LOCKS_GUARD = threading.Lock()
_HELD_LOCKS = threading.local()


def _thread_lock(path: Path) -> threading.RLock:
    key = os.path.normcase(str(path.resolve()))
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


class InterProcessLock:
    """Bloqueo exclusivo de archivo compatible con Windows y POSIX.

    El bloqueo del sistema operativo se complementa con un ``RLock`` local.
    Esto importa en POSIX, donde los locks pertenecen al proceso, y permite
    reutilizar el mismo lock de forma segura desde llamadas anidadas.
    """

    def __init__(self, path: str | Path, *, timeout: float = 15.0) -> None:
        self.path = Path(path)
        self.timeout = float(timeout)
        self._stream = None
        self._local = _thread_lock(self.path)
        self._key = os.path.normcase(str(self.path.resolve()))
        self._acquisitions = 0

    def acquire(self) -> InterProcessLock:
        deadline = time.monotonic() + max(0.0, self.timeout)
        self._local.acquire()
        held = getattr(_HELD_LOCKS, "paths", None)
        if held is None:
            held = _HELD_LOCKS.paths = {}
        if held.get(self._key, 0):
            held[self._key] += 1
            self._acquisitions += 1
            return self
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._stream = self.path.open("a+b")
            self._ensure_lock_byte()
            while True:
                try:
                    self._lock_os()
                    held[self._key] = 1
                    self._acquisitions += 1
                    return self
                except (BlockingIOError, OSError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"timeout esperando el bloqueo de datos: {self.path}")
                    time.sleep(0.05)
        except Exception:
            if self._stream is not None:
                self._stream.close()
                self._stream = None
            self._local.release()
            raise

    def release(self) -> None:
        held = getattr(_HELD_LOCKS, "paths", {})
        if self._acquisitions <= 0 or not held.get(self._key):
            raise RuntimeError(f"bloqueo no adquirido: {self.path}")
        self._acquisitions -= 1
        if held[self._key] > 1:
            held[self._key] -= 1
            self._local.release()
            return
        try:
            if self._stream is not None:
                try:
                    self._unlock_os()
                finally:
                    self._stream.close()
                    self._stream = None
        finally:
            held.pop(self._key, None)
            self._local.release()

    def _ensure_lock_byte(self) -> None:
        assert self._stream is not None
        self._stream.seek(0, os.SEEK_END)
        if self._stream.tell() == 0:
            self._stream.write(b"\0")
            self._stream.flush()
        self._stream.seek(0)

    def _lock_os(self) -> None:
        assert self._stream is not None
        if os.name == "nt":
            import msvcrt

            self._stream.seek(0)
            msvcrt.locking(self._stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_os(self) -> None:
        assert self._stream is not None
        if os.name == "nt":
            import msvcrt

            self._stream.seek(0)
            msvcrt.locking(self._stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)

    def __enter__(self) -> InterProcessLock:
        return self.acquire()

    def __exit__(self, *_args) -> None:
        self.release()


def lock_path(path: str | Path) -> Path:
    target = Path(path)
    return target.with_name(target.name + ".lock")


@contextmanager
def locked_file(path: str | Path, *, timeout: float = 15.0) -> Iterator[None]:
    with InterProcessLock(lock_path(path), timeout=timeout):
        yield


@contextmanager
def locked_files(
    paths: list[str | Path] | tuple[str | Path, ...], *, timeout: float = 15.0
) -> Iterator[None]:
    """Adquiere varios locks siempre en el mismo orden para evitar deadlocks."""

    # `normcase` también elimina duplicados que solo difieren en mayúsculas
    # en Windows. Adquirirlos dos veces sería trabajo innecesario y podría
    # confundir el conteo reentrante.
    unique_paths = {
        os.path.normcase(str(Path(item).resolve())): Path(item).resolve() for item in paths
    }
    locks = [
        InterProcessLock(lock_path(unique_paths[key]), timeout=timeout)
        for key in sorted(unique_paths)
    ]
    acquired: list[InterProcessLock] = []
    try:
        for lock in locks:
            lock.acquire()
            acquired.append(lock)
        yield
    finally:
        for lock in reversed(acquired):
            lock.release()


def transactional_method(method):
    """Protege métodos de almacenes que exponen ``self.path``."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with locked_file(self.path):
            return method(self, *args, **kwargs)

    return wrapper


def transactional_file(path: str | Path):
    """Decora una función completa con el lock de un archivo conocido."""

    def decorate(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            with locked_file(path):
                return function(*args, **kwargs)

        return wrapper

    return decorate


def transactional_path_argument(
    name: str, *, index: int = 0, transform: Callable[[Any], str | Path] = Path
):
    """Bloquea la ruta recibida por un parámetro de una función."""

    def decorate(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            value = kwargs[name] if name in kwargs else args[index]
            with locked_file(transform(value)):
                return function(*args, **kwargs)

        return wrapper

    return decorate


def atomic_write_bytes(path: str | Path, payload: bytes) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def atomic_write_text(path: str | Path, value: str, *, encoding: str = "utf-8") -> Path:
    return atomic_write_bytes(path, value.encode(encoding))


def atomic_write_json(
    path: str | Path,
    value: Any,
    *,
    indent: int | None = 2,
    sort_keys: bool = False,
) -> Path:
    """Serializa JSON UTF-8 de forma uniforme y lo reemplaza atómicamente."""

    payload = json.dumps(
        value,
        indent=indent,
        ensure_ascii=False,
        sort_keys=sort_keys,
    )
    return atomic_write_text(path, payload + "\n")


def load_json_unlocked(path: str | Path, default: Callable[[], T]) -> T:
    target = Path(path)
    if not target.exists():
        return default()
    return json.loads(target.read_text(encoding="utf-8"))


def update_json(
    path: str | Path,
    default: Callable[[], T],
    update: Callable[[T], Any],
    *,
    validate: Callable[[T], None] | None = None,
    indent: int = 2,
) -> T:
    """Ejecuta una transacción JSON exclusiva y devuelve el valor guardado."""

    target = Path(path)
    with locked_file(target):
        value = load_json_unlocked(target, default)
        replacement = update(value)
        if replacement is not None:
            value = replacement
        if validate is not None:
            validate(value)
        atomic_write_json(target, value, indent=indent)
        return value
