"""Lectura, escritura y actualización segura de archivos de datos."""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar
from weakref import WeakValueDictionary

T = TypeVar("T")
JSON_EXTENSIONS = {".json", ".config", ".lang", ".db"}
TEXT_EXTENSIONS = {".txt", ".log"}

_THREAD_LOCKS: WeakValueDictionary[str, threading.RLock] = WeakValueDictionary()
_THREAD_LOCKS_GUARD = threading.Lock()


def _thread_lock(path: Path) -> threading.RLock:
    key = os.path.normcase(str(path.resolve()))
    with _THREAD_LOCKS_GUARD:
        return _THREAD_LOCKS.setdefault(key, threading.RLock())


class FileLock:
    """Bloqueo de archivo sencillo compatible con Windows y POSIX."""

    def __init__(self, path: str | Path, *, timeout: float = 15.0) -> None:
        self.path = Path(path)
        self.timeout = float(timeout)
        self._stream = None
        self._local = _thread_lock(self.path)

    def acquire(self) -> FileLock:
        deadline = time.monotonic() + max(0.0, self.timeout)
        self._local.acquire()
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._stream = self.path.open("a+b")
            if self._stream.seek(0, os.SEEK_END) == 0:
                self._stream.write(b"\0")
                self._stream.flush()
            while True:
                try:
                    self._lock_os()
                    return self
                except (BlockingIOError, OSError):
                    if time.monotonic() >= deadline:
                        raise TimeoutError(f"timeout esperando el bloqueo: {self.path}")
                    time.sleep(0.05)
        except Exception:
            if self._stream is not None:
                self._stream.close()
                self._stream = None
            self._local.release()
            raise

    def release(self) -> None:
        if self._stream is None:
            raise RuntimeError(f"bloqueo no adquirido: {self.path}")
        try:
            self._unlock_os()
            self._stream.close()
            self._stream = None
        finally:
            self._local.release()

    def _lock_os(self) -> None:
        assert self._stream is not None
        self._stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_os(self) -> None:
        assert self._stream is not None
        self._stream.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)

    def __enter__(self) -> FileLock:
        return self.acquire()

    def __exit__(self, *_args: object) -> None:
        self.release()


def lock_path(path: str | Path) -> Path:
    target = Path(path)
    return target.with_name(target.name + ".lock")


@contextmanager
def locked_file(path: str | Path, *, timeout: float = 15.0) -> Iterator[None]:
    with FileLock(lock_path(path), timeout=timeout):
        yield


def atomic_write_bytes(path: str | Path, payload: bytes) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        return target.resolve()
    finally:
        temporary.unlink(missing_ok=True)


def write_text(path: str | Path, value: str, *, encoding: str = "utf-8") -> Path:
    return atomic_write_bytes(path, value.encode(encoding))


def write_json(path: str | Path, value: Any, *, indent: int = 2) -> Path:
    payload = json.dumps(value, indent=indent, ensure_ascii=False) + "\n"
    return write_text(path, payload)


def read(path: str | Path, default: T | None = None) -> Any | T:
    """Lee JSON para .json/.config/.lang/.db y texto para .txt/.log."""
    target = Path(path)
    if not target.exists():
        return default
    suffix = target.suffix.casefold()
    if suffix in JSON_EXTENSIONS:
        return json.loads(target.read_text(encoding="utf-8"))
    if suffix in TEXT_EXTENSIONS:
        return target.read_text(encoding="utf-8")
    raise ValueError(f"tipo de archivo no compatible: {target.suffix or '(sin extensión)'}")


def write(path: str | Path, value: Any) -> Path:
    """Escribe el formato adecuado según la extensión del archivo."""
    suffix = Path(path).suffix.casefold()
    if suffix in JSON_EXTENSIONS:
        return write_json(path, value)
    if suffix in TEXT_EXTENSIONS:
        if not isinstance(value, str):
            raise TypeError("los archivos de texto requieren un valor str")
        return write_text(path, value)
    raise ValueError(f"tipo de archivo no compatible: {suffix or '(sin extensión)'}")


def update_json(
    path: str | Path,
    default: Callable[[], T],
    update: Callable[[T], T | None],
) -> T:
    """Lee, modifica y guarda JSON dentro de una única transacción."""
    target = Path(path)
    if target.suffix.casefold() not in JSON_EXTENSIONS:
        raise ValueError("update_json solo admite .json, .config, .lang y .db")
    with locked_file(target):
        value = read(target, default())
        replacement = update(value)
        if replacement is not None:
            value = replacement
        write_json(target, value)
        return value
