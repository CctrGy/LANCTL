from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock

from app.core.paths import application_path


ICON_WIDTH = 125
ICON_HEIGHT = 125
ICON_DIRECTORY = "data/lc/icons"
ICON_REGISTRY = "icons.json"
ICON_ID = re.compile(r"^[a-z][a-z0-9]*(?:[._-][a-z0-9]+)*$")


@dataclass(frozen=True, slots=True)
class IconEntry:
    icon_id: str
    name: str
    filename: str
    width: int
    height: int
    checksum: str
    category: str = "general"
    tags: tuple[str, ...] = ()
    owner: str = "LANCTL"
    created: str = ""
    path: Path | None = None

    def to_registry(self) -> dict:
        return {
            "id": self.icon_id, "name": self.name, "file": self.filename,
            "width": self.width, "height": self.height,
            "checksum": self.checksum, "category": self.category,
            "tags": list(self.tags), "owner": self.owner, "created": self.created,
        }


class IconManager:
    """Catálogo gráfico sin dependencia de CLI, TUI ni librerías de imagen."""

    def __init__(self, directory: str | Path | None = None) -> None:
        self.directory = application_path(directory or ICON_DIRECTORY)
        self.registry_path = self.directory / ICON_REGISTRY
        self.icons: dict[str, IconEntry] = {}
        self.providers: dict[str, set[str]] = {}
        self.errors: list[dict[str, str]] = []
        self.initialized = False
        self._lock = RLock()

    def initialize(self) -> None:
        with self._lock:
            if self.initialized:
                return
            self.directory.mkdir(parents=True, exist_ok=True)
            previous = self._read_registry()
            for path in sorted(self.directory.iterdir()):
                if not path.is_file() or path.suffix.casefold() not in (".jpg", ".jpeg"):
                    continue
                icon_id = path.stem.casefold()
                saved = previous.get(icon_id, {})
                try:
                    _validate_id(icon_id)
                    entry = self._entry_from_file(
                        path, icon_id=icon_id,
                        name=str(saved.get("name") or path.stem),
                        category=str(saved.get("category") or "general"),
                        tags=tuple(saved.get("tags", [])), owner="LANCTL",
                        created=str(saved.get("created") or _now()),
                    )
                    self._add(entry)
                except ValueError as error:
                    self.errors.append({"file": path.name, "error": str(error)})
            self._save_registry()
            self.initialized = True

    def register(
        self, source: str | Path, *, icon_id: str | None = None,
        name: str = "", category: str = "general", tags=(), owner: str = "LANCTL",
        overwrite: bool = False,
    ) -> IconEntry:
        self.initialize()
        source_path = Path(source).expanduser().resolve()
        wanted = (icon_id or source_path.stem).strip().casefold()
        _validate_id(wanted)
        if source_path.suffix.casefold() not in (".jpg", ".jpeg"):
            raise ValueError("el icono debe usar la extensión .jpg o .jpeg")
        width, height = jpeg_dimensions(source_path)
        _validate_dimensions(width, height)
        if wanted in self.icons and not overwrite:
            raise ValueError(f"ya existe el icono: {wanted}")
        destination = self.directory / f"{wanted}.jpg"
        temporary = destination.with_suffix(".tmp")
        temporary.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, temporary)
        temporary.replace(destination)
        entry = self._entry_from_file(
            destination, icon_id=wanted, name=name or wanted,
            category=category, tags=tuple(tags), owner=owner, created=_now(),
        )
        self.icons[wanted] = entry
        self._save_registry()
        return entry

    def add_provider(
        self, owner: str, source: str | Path, *, icon_id: str,
        name: str = "", category: str = "general", tags=(),
    ) -> IconEntry:
        self.initialize()
        wanted = icon_id.casefold()
        _validate_id(wanted)
        if wanted in self.icons:
            raise ValueError(f"otro recurso ya proporciona el icono: {wanted}")
        path = Path(source).resolve()
        width, height = jpeg_dimensions(path)
        _validate_dimensions(width, height)
        entry = self._entry_from_file(
            path, icon_id=wanted, name=name or wanted, category=category,
            tags=tuple(tags), owner=owner, created=_now(),
        )
        self._add(entry)
        self.providers.setdefault(owner, set()).add(wanted)
        self._save_registry()
        return entry

    def remove_provider(self, owner: str) -> None:
        for icon_id in self.providers.pop(owner, set()):
            if self.icons.get(icon_id) and self.icons[icon_id].owner == owner:
                self.icons.pop(icon_id)
        if self.initialized:
            self._save_registry()

    def resolve(self, icon_id: str) -> Path:
        self.initialize()
        try:
            entry = self.icons[icon_id.casefold()]
        except KeyError as error:
            raise ValueError(f"icono no registrado: {icon_id}") from error
        if not entry.path or not entry.path.is_file():
            raise ValueError(f"archivo de icono no disponible: {icon_id}")
        return entry.path

    def get(self, icon_id: str) -> IconEntry:
        self.resolve(icon_id)
        return self.icons[icon_id.casefold()]

    def list(self, *, category: str | None = None, owner: str | None = None) -> list[IconEntry]:
        self.initialize()
        values = self.icons.values()
        if category:
            values = (item for item in values if item.category.casefold() == category.casefold())
        if owner:
            values = (item for item in values if item.owner.casefold() == owner.casefold())
        return sorted(values, key=lambda item: (item.category.casefold(), item.name.casefold()))

    def _entry_from_file(self, path: Path, **metadata) -> IconEntry:
        width, height = jpeg_dimensions(path)
        _validate_dimensions(width, height)
        return IconEntry(
            width=width, height=height, checksum=_sha256(path),
            filename=path.name, path=path.resolve(), **metadata,
        )

    def _add(self, entry: IconEntry) -> None:
        if entry.icon_id in self.icons:
            raise ValueError(f"identificador de icono duplicado: {entry.icon_id}")
        self.icons[entry.icon_id] = entry

    def _read_registry(self) -> dict[str, dict]:
        if not self.registry_path.exists() or not self.registry_path.stat().st_size:
            return {}
        try:
            document = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"catálogo de iconos JSON no válido: {self.registry_path}") from error
        return {str(item.get("id", "")).casefold(): item for item in document.get("icons", [])}

    def _save_registry(self) -> None:
        entries = sorted(
            self.icons.values(),
            key=lambda item: (item.owner != "LANCTL", item.category.casefold(), item.name.casefold()),
        )
        document = {
            "schemaVersion": 1,
            "format": {"mime": "image/jpeg", "width": ICON_WIDTH, "height": ICON_HEIGHT},
            "icons": [item.to_registry() for item in entries],
            "errors": list(self.errors),
        }
        temporary = self.registry_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.registry_path)


def jpeg_dimensions(path: str | Path) -> tuple[int, int]:
    """Lee SOF de JPEG sin decodificar píxeles ni depender de Pillow."""
    data = Path(path).read_bytes()
    if len(data) < 4 or data[:2] != b"\xff\xd8" or data[-2:] != b"\xff\xd9":
        raise ValueError("el archivo no es un JPEG completo")
    index = 2
    sof_markers = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
    while index < len(data) - 1:
        if data[index] != 0xFF:
            index += 1
            continue
        while index < len(data) and data[index] == 0xFF:
            index += 1
        if index >= len(data):
            break
        marker = data[index]
        index += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        if index + 2 > len(data):
            break
        length = int.from_bytes(data[index:index + 2], "big")
        if length < 2 or index + length > len(data):
            raise ValueError("segmento JPEG truncado")
        if marker in sof_markers:
            if length < 7:
                raise ValueError("cabecera SOF JPEG no válida")
            height = int.from_bytes(data[index + 3:index + 5], "big")
            width = int.from_bytes(data[index + 5:index + 7], "big")
            return width, height
        index += length
    raise ValueError("el JPEG no contiene dimensiones SOF")


def _validate_id(value: str) -> None:
    if not ICON_ID.fullmatch(value):
        raise ValueError("identificador de icono no válido")


def _validate_dimensions(width: int, height: int) -> None:
    if (width, height) != (ICON_WIDTH, ICON_HEIGHT):
        raise ValueError(f"el icono debe medir {ICON_WIDTH}x{ICON_HEIGHT}; recibido {width}x{height}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


_MANAGER: IconManager | None = None


def get_icon_manager() -> IconManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = IconManager()
    return _MANAGER


def initialize_icons() -> IconManager:
    manager = get_icon_manager()
    manager.initialize()
    return manager
