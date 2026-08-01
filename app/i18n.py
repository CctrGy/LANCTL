from __future__ import annotations

import json
import locale
import re
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any

from app.core.paths import application_path


LANG_SCHEMA_VERSION = 1
LANGUAGES_DIRECTORY = "data/lc/languajes"  # nombre histórico de languajes conservado
LANGUAGES_REGISTRY = "languajes.json"
KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*(?:\.[A-Z][A-Z0-9_]*){2,}$")


ENGLISH_STRINGS: dict[str, str] = {
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
        if self.directory.exists():
            for path in sorted(self.directory.glob("*.lang")):
                catalog = self.load_file(path)
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
            document = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError(f"Invalid language JSON: {source}") from error
        meta = document.get("meta", {})
        strings = document.get("strings", {})
        if int(document.get("schemaVersion", 0)) != LANG_SCHEMA_VERSION or not isinstance(strings, dict):
            raise ValueError(f"Invalid language schema: {source}")
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
            code, str(meta.get("name") or code), str(meta.get("nativeName") or meta.get("name") or code),
            str(meta.get("region", "")), str(meta.get("version", "1.0")),
            str(meta.get("author", "")), source, normalized, owner,
        )

    def install(self, path: str | Path) -> LanguageCatalog:
        catalog = self.load_file(path)
        current = self.catalogs.get(catalog.code)
        destination = (
            current.path if current and current.path and current.path.parent == self.directory
            else self.directory / f"{_safe_filename(catalog.name)}.lang"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp")
        temporary.write_text(Path(path).read_text(encoding="utf-8"), encoding="utf-8")
        temporary.replace(destination)
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
        aliases = {"english": "en", "inglés": "en", "ingles": "en", "spanish": "es", "español": "es", "espanol": "es"}
        wanted = aliases.get(wanted, wanted)
        if wanted in self.catalogs:
            return wanted
        base = wanted.split("-", 1)[0]
        if base in self.catalogs:
            return base
        return "en"

    def translate(self, key: str, **values: Any) -> str:
        catalog = self.catalogs.get(self._selected, self.catalogs["en"])
        template = catalog.strings.get(key) or self.catalogs["en"].strings.get(key) or key
        try:
            return template.format(**values)
        except (KeyError, ValueError) as error:
            raise ValueError(f"Invalid translation arguments for {key}: {error}") from error

    def validate(self, path: str | Path) -> dict[str, Any]:
        catalog = self.load_file(path)
        total = len(ENGLISH_STRINGS)
        translated = sum(1 for key in ENGLISH_STRINGS if key in catalog.strings)
        return {"valid": True, "catalog": catalog, "translated": translated, "total": total, "coverage": round(translated * 100 / max(1, total), 1)}

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
        self.catalogs["en"] = LanguageCatalog("en", "English", "English", "International", "1.0", "LANCTL", None, dict(ENGLISH_STRINGS))

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
        data = {"schemaVersion": 1, "selected": self._selected, "fallback": "en", "languages": [
            {"code": item.code, "name": item.name, "nativeName": item.native_name,
             "file": item.path.name if item.path and item.path.parent == self.directory else None,
             "owner": item.owner, "version": item.version}
            for item in self.list()
        ]}
        temporary = self.registry_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        temporary.replace(self.registry_path)


def _english_document() -> dict[str, Any]:
    return {"schemaVersion": 1, "meta": {"code": "en", "name": "English", "nativeName": "English", "region": "International", "version": "1.0", "author": "LANCTL"}, "strings": ENGLISH_STRINGS}


def spanish_document() -> dict[str, Any]:
    return {"schemaVersion": 1, "meta": {"code": "es", "name": "Spanish", "nativeName": "Español", "region": "España", "version": "1.0", "author": "LANCTL"}, "strings": SPANISH_STRINGS}


def _write_catalog(path: Path, document: dict) -> None:
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _safe_filename(value: str) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", value.casefold()).strip("-") or "language"


def _placeholders(value: str) -> set[str]:
    return set(re.findall(r"(?<!\{)\{([A-Za-z_][A-Za-z0-9_]*)[^}]*\}(?!\})", value))


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
            from app.core.config import load_config
            selected = str(load_config().get("language", "en"))
        except (OSError, ValueError):
            selected = "en"
    manager.initialize(selected)
    return manager


def t(key: str, **values: Any) -> str:
    return get_language_manager().translate(key, **values)
