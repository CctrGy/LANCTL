from __future__ import annotations

import json
import re
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from lanctl.core.file_transaction import atomic_write_json, atomic_write_text, locked_file
from lanctl.core.paths import application_path
from lanctl.shared.language_contract import (
    KEY_PATTERN,
    flatten_document,
    placeholders,
    read_document,
    structured_document,
)

_LANGUAGE_OVERRIDE = ContextVar("lanctl_language_override", default=None)
LANG_SCHEMA_VERSION = 2
LANGUAGES_DIRECTORY = "data/lc/languajes"  # grafía histórica conservada por compatibilidad
LANGUAGES_REGISTRY = "languajes.json"
# Historical public keys kept for compatibility; catalog edits cannot alter technical output.
TECHNICAL_KEYS = frozenset({"LANCTL.PROJECT.PATH.DEFAULT", "LANCTL.PLUGIN.LOG.ACTION"})


ENGLISH_STRINGS: dict[str, str] = {
    "LANCTL.INVENTORY.MANUAL.TITLE": "Add device",
    "LANCTL.INVENTORY.MANUAL.SEARCH": "Search",
    "LANCTL.INVENTORY.MANUAL.ADD": "Add",
    "LANCTL.INVENTORY.MANUAL.CANCEL": "Cancel",
    "LANCTL.INVENTORY.MANUAL.NAME": "Name",
    "LANCTL.INVENTORY.MANUAL.ALIAS": "Alias",
    "LANCTL.INVENTORY.MANUAL.IDF": "IDF (unique)",
    "LANCTL.INVENTORY.MANUAL.IP": "IPv4 address (optional)",
    "LANCTL.INVENTORY.MANUAL.MAC": "MAC (optional; may be completed by a scan)",
    "LANCTL.INVENTORY.MANUAL.DESCRIPTION": "Description",
    "LANCTL.INVENTORY.MANUAL.CREATED": "Device added",
    "LANCTL.INVENTORY.MANUAL.STALE": "The project changed. Close and reopen the form.",
    "LANCTL.INVENTORY.MANUAL.FAILED": "Could not add the device",
    "LANCTL.COMMON.VALUE.NONE": "-",
    "LANCTL.COMMON.ACTION.HELP": "Show this help and exit.",
    "LANCTL.COMMON.ACTION.LIST": "List",
    "LANCTL.COMMON.ACTION.INFO": "Information",
    "LANCTL.COMMON.ACTION.ENABLE": "Enable",
    "LANCTL.COMMON.ACTION.DISABLE": "Disable",
    "LANCTL.COMMON.ACTION.RELOAD": "Reload",
    "LANCTL.COMMON.ACTION.REMOVE": "Remove",
    "LANCTL.COMMON.STATUS.OK": "OK",
    "LANCTL.COMMON.STATUS.PENDING": "PENDING",
    "LANCTL.COMMON.STATUS.ERROR": "ERROR",
    "LANCTL.COMMON.STATUS.ACTIVE": "ACTIVE",
    "LANCTL.COMMON.STATUS.INACTIVE": "INACTIVE",
    "LANCTL.PARSER.SECTION.USAGE": "Usage:",
    "LANCTL.PARSER.SECTION.ARGUMENTS": "Arguments:",
    "LANCTL.PARSER.SECTION.OPTIONS": "Options:",
    "LANCTL.PARSER.ERROR.INVALID_CHOICE": "invalid choice",
    "LANCTL.CORE.APP.DESCRIPTION": "Logical control of LAN devices and infrastructure.",
    "LANCTL.CORE.APP.GUI_RESERVED": "Open the LANCTL graphical interface.",
    "LANCTL.CORE.APP.CLI_HELP": "Open the persistent interactive LANCTL terminal.",
    "LANCTL.CORE.APP.TUI_HELP": "Open the advanced full-screen terminal interface.",
    "LANCTL.CORE.APP.GUI_PENDING": "The graphical interface is not available yet. Use 'lanctl --cli' to open the interactive terminal.",
    "LANCTL.CORE.APP.CANCELLED": "Operation cancelled.",
    "LANCTL.CLI.HEADER.TITLE": "LANCTL CLI",
    "LANCTL.CLI.HEADER.INTRO": "Type 'help' to list commands and 'exit' to quit.",
    "LANCTL.CLI.ERROR.NO_SELECTION": "No device is selected.",
    "LANCTL.CLI.ERROR.SELECT_USAGE": "usage: select DEVICE",
    "LANCTL.CLI.STATUS.SELECTED": "SELECTED",
    "LANCTL.CLI.STATUS.SELECTION": "SELECTION",
    "LANCTL.CLI.STATUS.DESELECTED": "Device context cleared.",
    "LANCTL.LANGUAGE.COMMAND.HELP": "Manage LANCTL interface languages.",
    "LANCTL.LANGUAGE.ACTION.LIST": "List installed languages.",
    "LANCTL.LANGUAGE.ACTION.USE": "Select the interface language.",
    "LANCTL.LANGUAGE.ACTION.INFO": "Show language metadata and coverage.",
    "LANCTL.LANGUAGE.ACTION.INSTALL": "Install or update a .lang JSON catalog.",
    "LANCTL.LANGUAGE.ACTION.VALIDATE": "Validate a .lang catalog.",
    "LANCTL.LANGUAGE.ACTION.EXPORT": "Export the English template for translation.",
    "LANCTL.LANGUAGE.FIELD.CODE": "CODE",
    "LANCTL.LANGUAGE.FIELD.LANGUAGE": "LANGUAGE",
    "LANCTL.LANGUAGE.FIELD.REGION": "REGION",
    "LANCTL.LANGUAGE.FIELD.COVERAGE": "COVERAGE",
    "LANCTL.LANGUAGE.FIELD.ACTIVE": "ACTIVE",
    "LANCTL.LANGUAGE.STATUS.INSTALLED": "LANGUAGE INSTALLED",
    "LANCTL.LANGUAGE.STATUS.SELECTED": "LANGUAGE SELECTED",
    "LANCTL.LANGUAGE.STATUS.VALID": "LANGUAGE VALID",
    "LANCTL.LANGUAGE.STATUS.EXPORTED": "TEMPLATE EXPORTED",
    "LANCTL.LANGUAGE.ERROR.NOT_FOUND": "Language not installed: {language}",
    "LANCTL.LANGUAGE.ERROR.INVALID_JSON": "Invalid language JSON: {path}",
    "LANCTL.LANGUAGE.ERROR.INVALID_KEY": "Invalid translation key: {key}",
    "LANCTL.LANGUAGE.ERROR.PLACEHOLDER": "Placeholder mismatch in {key}",
    "LANCTL.LANGUAGE.ERROR.DUPLICATE_CODE": "Language code already provided by another catalog: {code}",
    "LANCTL.LANGUAGE.INFO.FALLBACK": "Missing translations automatically fall back to English.",
    "LANCTL.PROJECT.PATH.DEFAULT": "%USERPROFILE%\\Documents\\LanCTL",
    "LANCTL.PLUGIN.LOG.ACTION": "PLUGIN id={plugin_id} action={action} target={target} result={result}",
}


SPANISH_STRINGS: dict[str, str] = {
    "LANCTL.INVENTORY.MANUAL.TITLE": "Añadir elemento",
    "LANCTL.INVENTORY.MANUAL.SEARCH": "Buscar",
    "LANCTL.INVENTORY.MANUAL.ADD": "Añadir",
    "LANCTL.INVENTORY.MANUAL.CANCEL": "Cancelar",
    "LANCTL.INVENTORY.MANUAL.NAME": "Nombre",
    "LANCTL.INVENTORY.MANUAL.ALIAS": "Alias",
    "LANCTL.INVENTORY.MANUAL.IDF": "IDF (único)",
    "LANCTL.INVENTORY.MANUAL.IP": "Dirección IPv4 (opcional)",
    "LANCTL.INVENTORY.MANUAL.MAC": "MAC (opcional; puede completarse al escanear)",
    "LANCTL.INVENTORY.MANUAL.DESCRIPTION": "Descripción",
    "LANCTL.INVENTORY.MANUAL.CREATED": "Elemento añadido",
    "LANCTL.INVENTORY.MANUAL.STALE": "El proyecto cambió. Cierra el formulario y vuelve a abrirlo.",
    "LANCTL.INVENTORY.MANUAL.FAILED": "No se pudo añadir el elemento",
    "LANCTL.COMMON.VALUE.NONE": "-",
    "LANCTL.COMMON.ACTION.HELP": "Muestra esta ayuda y termina.",
    "LANCTL.COMMON.ACTION.LIST": "Listar",
    "LANCTL.COMMON.ACTION.INFO": "Información",
    "LANCTL.COMMON.ACTION.ENABLE": "Activar",
    "LANCTL.COMMON.ACTION.DISABLE": "Desactivar",
    "LANCTL.COMMON.ACTION.RELOAD": "Recargar",
    "LANCTL.COMMON.ACTION.REMOVE": "Eliminar",
    "LANCTL.COMMON.STATUS.OK": "CORRECTO",
    "LANCTL.COMMON.STATUS.PENDING": "PENDIENTE",
    "LANCTL.COMMON.STATUS.ERROR": "ERROR",
    "LANCTL.COMMON.STATUS.ACTIVE": "ACTIVO",
    "LANCTL.COMMON.STATUS.INACTIVE": "INACTIVO",
    "LANCTL.PARSER.SECTION.USAGE": "Uso:",
    "LANCTL.PARSER.SECTION.ARGUMENTS": "Argumentos:",
    "LANCTL.PARSER.SECTION.OPTIONS": "Opciones:",
    "LANCTL.PARSER.ERROR.INVALID_CHOICE": "opción no válida",
    "LANCTL.CORE.APP.DESCRIPTION": "Control lógico de dispositivos e infraestructuras LAN.",
    "LANCTL.CORE.APP.GUI_RESERVED": "Abre la interfaz gráfica de LANCTL.",
    "LANCTL.CORE.APP.CLI_HELP": "Abre la terminal interactiva persistente de LANCTL.",
    "LANCTL.CORE.APP.TUI_HELP": "Abre la interfaz avanzada de terminal a pantalla completa.",
    "LANCTL.CORE.APP.GUI_PENDING": "La interfaz gráfica todavía no está disponible. Usa 'lanctl --cli' para abrir la terminal interactiva.",
    "LANCTL.CORE.APP.CANCELLED": "Operación cancelada.",
    "LANCTL.CLI.HEADER.TITLE": "LANCTL CLI",
    "LANCTL.CLI.HEADER.INTRO": "Escribe 'help' para ver los comandos y 'exit' para salir.",
    "LANCTL.CLI.ERROR.NO_SELECTION": "No hay ningún elemento seleccionado.",
    "LANCTL.CLI.ERROR.SELECT_USAGE": "usa: select ELEMENTO",
    "LANCTL.CLI.STATUS.SELECTED": "SELECCIONADO",
    "LANCTL.CLI.STATUS.SELECTION": "SELECCIÓN",
    "LANCTL.CLI.STATUS.DESELECTED": "Contexto de elemento eliminado.",
    "LANCTL.LANGUAGE.COMMAND.HELP": "Gestiona los idiomas de la interfaz de LANCTL.",
    "LANCTL.LANGUAGE.ACTION.LIST": "Lista los idiomas instalados.",
    "LANCTL.LANGUAGE.ACTION.USE": "Selecciona el idioma de la interfaz.",
    "LANCTL.LANGUAGE.ACTION.INFO": "Muestra metadatos y cobertura del idioma.",
    "LANCTL.LANGUAGE.ACTION.INSTALL": "Instala o actualiza un catálogo JSON .lang.",
    "LANCTL.LANGUAGE.ACTION.VALIDATE": "Valida un catálogo .lang.",
    "LANCTL.LANGUAGE.ACTION.EXPORT": "Exporta la plantilla inglesa para traducir.",
    "LANCTL.LANGUAGE.FIELD.CODE": "CÓDIGO",
    "LANCTL.LANGUAGE.FIELD.LANGUAGE": "IDIOMA",
    "LANCTL.LANGUAGE.FIELD.REGION": "REGIÓN",
    "LANCTL.LANGUAGE.FIELD.COVERAGE": "COBERTURA",
    "LANCTL.LANGUAGE.FIELD.ACTIVE": "ACTIVO",
    "LANCTL.LANGUAGE.STATUS.INSTALLED": "IDIOMA INSTALADO",
    "LANCTL.LANGUAGE.STATUS.SELECTED": "IDIOMA SELECCIONADO",
    "LANCTL.LANGUAGE.STATUS.VALID": "IDIOMA VÁLIDO",
    "LANCTL.LANGUAGE.STATUS.EXPORTED": "PLANTILLA EXPORTADA",
    "LANCTL.LANGUAGE.ERROR.NOT_FOUND": "Idioma no instalado: {language}",
    "LANCTL.LANGUAGE.ERROR.INVALID_JSON": "JSON de idioma no válido: {path}",
    "LANCTL.LANGUAGE.ERROR.INVALID_KEY": "Clave de traducción no válida: {key}",
    "LANCTL.LANGUAGE.ERROR.PLACEHOLDER": "Los placeholders no coinciden en {key}",
    "LANCTL.LANGUAGE.ERROR.DUPLICATE_CODE": "Otro catálogo ya proporciona el código: {code}",
    "LANCTL.LANGUAGE.INFO.FALLBACK": "Las traducciones ausentes utilizan automáticamente el inglés.",
    "LANCTL.PROJECT.PATH.DEFAULT": "%USERPROFILE%\\Documents\\LanCTL",
    "LANCTL.PLUGIN.LOG.ACTION": "PLUGIN id={plugin_id} acción={action} objetivo={target} resultado={result}",
}


MESSAGE_LOCATIONS = {
    key: ("LANIP", "GUI") for key in ENGLISH_STRINGS if key.startswith("LANCTL.INVENTORY.MANUAL.")
}
_UI_READY = False
_UI_LOCK = RLock()
_SOURCE_LABEL_KEYS = {}


def _ensure_ui_messages():
    # Technical worker processes import i18n through console/error contracts.
    # Do not load thousands of UI templates into their bounded address space.
    global _UI_READY
    if _UI_READY:
        return
    with _UI_LOCK:
        if _UI_READY:
            return
        from lanctl.shared.ui_messages import UI_LOCATIONS, UI_MESSAGES

        dict.update(ENGLISH_STRINGS, {key: pair[0] for key, pair in UI_MESSAGES.items()})
        dict.update(SPANISH_STRINGS, {key: pair[1] for key, pair in UI_MESSAGES.items()})
        MESSAGE_LOCATIONS.update(UI_LOCATIONS)
        _SOURCE_LABEL_KEYS.update(
            {value: key for key, value in dict.items(SPANISH_STRINGS) if key not in TECHNICAL_KEYS}
        )
        _UI_READY = True


class _CatalogStrings(dict):
    """Compatible dictionary that loads the full catalog on first public read."""

    def __getitem__(self, key):
        _ensure_ui_messages()
        return super().__getitem__(key)

    def get(self, key, default=None):
        _ensure_ui_messages()
        return super().get(key, default)

    def __iter__(self):
        _ensure_ui_messages()
        return super().__iter__()

    def __len__(self):
        _ensure_ui_messages()
        return super().__len__()

    def __contains__(self, key):
        _ensure_ui_messages()
        return super().__contains__(key)

    def keys(self):
        _ensure_ui_messages()
        return super().keys()

    def values(self):
        _ensure_ui_messages()
        return super().values()

    def items(self):
        _ensure_ui_messages()
        return super().items()

    def copy(self):
        _ensure_ui_messages()
        return super().copy()


ENGLISH_STRINGS = _CatalogStrings(ENGLISH_STRINGS)
SPANISH_STRINGS = _CatalogStrings(SPANISH_STRINGS)


class TranslatedText(str):
    """A display string retaining a language-independent operational log value."""

    def __new__(cls, display: str, canonical: str, source: str | None = None):
        instance = super().__new__(cls, display)
        instance.canonical_text = canonical
        instance.source_text = source if source is not None else display
        return instance

    def __getnewargs__(self):
        return str(self), self.canonical_text, self.source_text


@dataclass(frozen=True, slots=True)
class LanguageCatalog:
    code: str
    name: str
    native_name: str
    region: str
    version: str
    author: str
    path: Path | None
    strings: dict[str, str]
    owner: str = "LANCTL"


class LanguageManager:
    def __init__(self, directory: str | Path | None = None) -> None:
        _ensure_ui_messages()
        self.directory = application_path(directory or LANGUAGES_DIRECTORY)
        self.registry_path = self.directory / LANGUAGES_REGISTRY
        self.catalogs: dict[str, LanguageCatalog] = {}
        self.providers: dict[str, set[str]] = {}
        self._lock = RLock()
        self._selected = "en"
        self.initialized = False
        self._register_builtin()

    def initialize(self, selected: str = "en") -> None:
        with self._lock:
            if self.initialized:
                self._selected = self.resolve_code(selected)
                return
            self.directory.mkdir(parents=True, exist_ok=True)
            self._migrate_legacy_names()
            self._write_english_if_missing()
            self.discover()
            self._selected = self.resolve_code(selected)
            self._save_registry()
            self.initialized = True

    def discover(self) -> list[LanguageCatalog]:
        built_in = self.catalogs["en"]
        self.catalogs = {"en": built_in}
        seen = set()
        if self.directory.exists():
            for path in sorted(self.directory.glob("*.lang")):
                catalog = self.load_file(path)
                if catalog.code in seen:
                    raise ValueError(f"Duplicate installed language code: {catalog.code}")
                seen.add(catalog.code)
                if catalog.code == "en":
                    self.catalogs["en"] = catalog
                elif catalog.code in self.catalogs:
                    raise ValueError(t("LANCTL.LANGUAGE.ERROR.DUPLICATE_CODE", code=catalog.code))
                else:
                    self.catalogs[catalog.code] = catalog
        return self.list()

    def load_file(self, path: str | Path, owner: str = "LANCTL") -> LanguageCatalog:
        source = Path(path).expanduser().resolve()
        if source.suffix.casefold() != ".lang":
            raise ValueError(f"Language catalog must use .lang: {source}")
        try:
            document = read_document(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid language JSON: {source}") from error
        meta = document.get("meta", {})
        strings = flatten_document(document)
        normalized: dict[str, str] = {}
        for key, value in strings.items():
            if not KEY_PATTERN.fullmatch(str(key)):
                raise ValueError(f"Invalid translation key: {key}")
            if not isinstance(value, str):
                raise ValueError(f"Translation must be text: {key}")
            _validate_placeholders(str(key), value)
            normalized[str(key)] = value
        code = str(meta.get("code", "")).strip().casefold().replace("_", "-")
        if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z0-9]{2,8})?", code):
            raise ValueError(f"Invalid language code: {code}")
        return LanguageCatalog(
            code,
            str(meta.get("name") or code),
            str(meta.get("nativeName") or meta.get("name") or code),
            str(meta.get("region", "")),
            str(meta.get("version", "1.0")),
            str(meta.get("author", "")),
            source,
            normalized,
            owner,
        )

    def install(self, path: str | Path) -> LanguageCatalog:
        catalog = self.load_file(path)
        current = self.catalogs.get(catalog.code)
        destination = (
            current.path
            if current and current.path and current.path.parent == self.directory
            else self.directory / f"{_safe_filename(catalog.name)}.lang"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        with locked_file(destination):
            if destination.exists() and self.load_file(destination).code != catalog.code:
                raise ValueError("Language filename already belongs to a different language")
            atomic_write_text(destination, Path(path).read_text(encoding="utf-8"))
        self.discover()
        self._save_registry()
        return self.catalogs[catalog.code]

    def add_provider(self, owner: str, path: str | Path) -> LanguageCatalog:
        catalog = self.load_file(path, owner=owner)
        if catalog.code in self.catalogs and self.catalogs[catalog.code].owner != owner:
            raise ValueError(f"Language code already provided: {catalog.code}")
        self.catalogs[catalog.code] = catalog
        self.providers.setdefault(owner, set()).add(catalog.code)
        return catalog

    def remove_provider(self, owner: str) -> None:
        for code in self.providers.pop(owner, set()):
            if self.catalogs.get(code) and self.catalogs[code].owner == owner:
                self.catalogs.pop(code)
        if self._selected not in self.catalogs:
            self._selected = "en"

    def select(self, language: str) -> LanguageCatalog:
        self._selected = self.resolve_code(language)
        self._save_registry()
        return self.catalogs[self._selected]

    def resolve_code(self, language: str) -> str:
        wanted = (language or "en").strip().casefold().replace("_", "-")
        aliases = {
            "english": "en",
            "inglés": "en",
            "ingles": "en",
            "spanish": "es",
            "español": "es",
            "espanol": "es",
        }
        wanted = aliases.get(wanted, wanted)
        if wanted in self.catalogs:
            return wanted
        base = wanted.split("-", 1)[0]
        if base in self.catalogs:
            return base
        return "en"

    def translate(self, key: str, **values: Any) -> str:
        catalog = self.catalogs.get(_LANGUAGE_OVERRIDE.get() or self._selected, self.catalogs["en"])
        template = (
            catalog.strings.get(key)
            or (self.catalogs.get(catalog.code.split("-", 1)[0], catalog).strings.get(key))
            or self.catalogs["en"].strings.get(key)
            or ENGLISH_STRINGS.get(key)
            or key
        )
        if key in TECHNICAL_KEYS:
            template = ENGLISH_STRINGS[key]
        try:
            display = template.format(**values)
            canonical_values = {
                name: getattr(value, "canonical_text", value) for name, value in values.items()
            }
            canonical = ENGLISH_STRINGS.get(key, template).format(**canonical_values)
            source_values = {
                name: getattr(value, "source_text", value) for name, value in values.items()
            }
            source = SPANISH_STRINGS.get(key, template).format(**source_values)
            return TranslatedText(display, canonical, source)
        except (KeyError, ValueError) as error:
            raise ValueError(f"Invalid translation arguments for {key}: {error}") from error

    def presentation_payload(self) -> dict[str, Any]:
        """Raw templates for explicit frontend bindings; never format user data here."""
        catalog = self.catalogs.get(_LANGUAGE_OVERRIDE.get() or self._selected, self.catalogs["en"])
        base = self.catalogs.get(catalog.code.split("-", 1)[0])
        strings = dict(ENGLISH_STRINGS)
        strings.update({key: value for key, value in self.catalogs["en"].strings.items() if value})
        if base:
            strings.update({key: value for key, value in base.strings.items() if value})
        strings.update({key: value for key, value in catalog.strings.items() if value})
        strings.update({key: ENGLISH_STRINGS[key] for key in TECHNICAL_KEYS})
        return {"code": catalog.code, "strings": strings}

    def validate(self, path: str | Path) -> dict[str, Any]:
        catalog = self.load_file(path)
        total = len(ENGLISH_STRINGS)
        translated = sum(1 for key in ENGLISH_STRINGS if key in catalog.strings)
        return {
            "valid": True,
            "catalog": catalog,
            "translated": translated,
            "total": total,
            "coverage": round(translated * 100 / max(1, total), 1),
        }

    def export_template(self, output: str | Path) -> Path:
        destination = Path(output).expanduser().resolve()
        if destination.suffix.casefold() != ".lang":
            destination = destination.with_suffix(".lang")
        destination.parent.mkdir(parents=True, exist_ok=True)
        _write_catalog(destination, _english_document())
        return destination

    def list(self) -> list[LanguageCatalog]:
        return sorted(self.catalogs.values(), key=lambda item: item.native_name.casefold())

    @property
    def selected(self) -> str:
        return self._selected

    def _register_builtin(self) -> None:
        self.catalogs["en"] = LanguageCatalog(
            "en",
            "English",
            "English",
            "International",
            "1.0",
            "LANCTL",
            None,
            dict(ENGLISH_STRINGS),
        )

    def _write_english_if_missing(self) -> None:
        target = self.directory / "english.lang"
        if not target.exists():
            _write_catalog(target, _english_document())

    def _migrate_legacy_names(self) -> None:
        legacy = self.directory / "eanglish.lang"
        correct = self.directory / "english.lang"
        if legacy.exists() and not correct.exists():
            if legacy.stat().st_size:
                legacy.replace(correct)
            else:
                legacy.unlink()

    def _save_registry(self) -> None:
        data = {
            "schemaVersion": 1,
            "selected": self._selected,
            "fallback": "en",
            "languages": [
                {
                    "code": item.code,
                    "name": item.name,
                    "nativeName": item.native_name,
                    "file": item.path.name
                    if item.path and item.path.parent == self.directory
                    else None,
                    "owner": item.owner,
                    "version": item.version,
                }
                for item in self.list()
            ],
        }
        with locked_file(self.registry_path):
            atomic_write_json(self.registry_path, data)


def _english_document() -> dict[str, Any]:
    _ensure_ui_messages()
    return structured_document(
        {
            "code": "en",
            "name": "English",
            "nativeName": "English",
            "region": "International",
            "version": "2.0",
            "author": "LANCTL",
        },
        ENGLISH_STRINGS,
        MESSAGE_LOCATIONS,
    )


def spanish_document() -> dict[str, Any]:
    _ensure_ui_messages()
    return structured_document(
        {
            "code": "es",
            "name": "Spanish",
            "nativeName": "Español",
            "region": "España",
            "version": "2.0",
            "author": "LANCTL",
        },
        SPANISH_STRINGS,
        MESSAGE_LOCATIONS,
    )


def _write_catalog(path: Path, document: dict) -> None:
    with locked_file(path):
        atomic_write_json(path, document)


def _safe_filename(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.casefold()).strip("-") or "language"


def _placeholders(value: str) -> set[str]:
    return placeholders(value)


def _validate_placeholders(key: str, value: str) -> None:
    expected = _placeholders(ENGLISH_STRINGS.get(key, value))
    if _placeholders(value) != expected:
        raise ValueError(f"Placeholder mismatch in {key}")


_MANAGER: LanguageManager | None = None


def get_language_manager() -> LanguageManager:
    global _MANAGER
    if _MANAGER is None:
        _MANAGER = LanguageManager()
    return _MANAGER


def initialize_language(selected: str | None = None) -> LanguageManager:
    manager = get_language_manager()
    if selected is None:
        try:
            from lanctl.core.config import load_config

            selected = str(load_config().get("language", "en"))
        except (OSError, ValueError) as error:
            from lanctl.core.errors import errors

            errors.from_exception(
                error,
                origin="LANCTL.I18N.Initialization",
                code="I18N.LANGUAGE.FALLBACK",
                level=14,
                details={"fallback": "en"},
                print_output=False,
            )
            selected = "en"
    manager.initialize(selected)
    return manager


def t(key: str, **values: Any) -> str:
    return get_language_manager().translate(key, **values)


@contextmanager
def language_context(code: str):
    """Temporarily select a presentation language without changing user settings."""
    token = _LANGUAGE_OVERRIDE.set(code)
    try:
        yield
    finally:
        _LANGUAGE_OVERRIDE.reset(token)


def translate_label(source: str) -> str:
    """Compatibility adapter for fixed, application-owned label metadata only.

    Do not use on user data, logs, exceptions or arbitrary rendered output.
    """
    _ensure_ui_messages()
    key = _SOURCE_LABEL_KEYS.get(source)
    return t(key) if key else source


def translate_specification(specification: dict) -> dict:
    """Copy UI metadata, localizing only declared display fields, never data IDs."""
    display_fields = frozenset({"label", "title", "help", "description", "confirmation"})

    def visit(value):
        if isinstance(value, list):
            return [visit(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {key: visit(item) for key, item in value.items()}
        for field in display_fields:
            source = value.get(field)
            if not isinstance(source, str):
                continue
            key = value.get(field + "Key")
            if isinstance(key, str) and KEY_PATTERN.fullmatch(key):
                manager = get_language_manager()
                if key in manager.presentation_payload()["strings"]:
                    result[field] = t(key)
                    continue
            result[field] = translate_label(source)
        return result

    return visit(specification)
