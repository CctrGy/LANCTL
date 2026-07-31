from __future__ import annotations

import json
from pathlib import Path


EXAMPLE_PLUGIN_ID = "lanctl.example.network-summary"

EXAMPLE_MANIFEST = {
    "schemaVersion": 1,
    "id": EXAMPLE_PLUGIN_ID,
    "name": "Network Summary Example",
    "version": "1.0.0",
    "description": "Ejemplo declarativo que resume el inventario LANCTL.",
    "author": "LANCTL",
    "entryPoint": "main.exec",
    "runtime": "isolated",
    "builtIn": True,
    "defaultEnabled": True,
    "lanctl": {"minimumVersion": "0.3.0", "maximumVersion": "0.x"},
    "permissions": ["command.register"],
    "capabilities": ["plugin", "commands", "analysis"],
}

EXAMPLE_API_MAP = {
    "extensions": [{
        "id": "lanctl.example.network-summary.command",
        "type": "command",
        "specification": {
            "name": "network-summary",
            "aliases": ["netsummary"],
            "help": "Resume los dispositivos almacenados sin escanear la red.",
            "action": "inventory.summary",
        },
    }]
}

PLUGIN_README = r"""# Desarrollo de complementos LANCTL (LCP 1.0)

Esta carpeta contiene los plugins instalados. No copies código aquí sin
verificarlo: usa `lanctl plugin install ARCHIVO.lcp`.

## Comandos de gestión

```bat
lanctl plugin list
lanctl plugin info ID
lanctl plugin verify ARCHIVO.lcp
lanctl plugin install ARCHIVO.lcp
lanctl plugin permissions ID
lanctl plugin enable ID --grant-all
lanctl plugin enable ID --grant-all --trust
lanctl plugin disable ID
lanctl plugin reload ID
lanctl plugin uninstall ID
lanctl plugin extensions
lanctl plugin pack DIRECTORIO SALIDA.lcp
```

## Estructura mínima

```text
plugin.info
main.exec                    # solo runtime=trusted
api/api.map
api/events.schema
api/events.registry
api/hooks/*.hook
assets/lang/*.lang
modules/
config/default.config
meta/version
meta/created
meta/checksum
meta/signature               # opcional, Ed25519
meta/public-key.pem          # requerido si existe signature
```

## plugin.info

Campos: `schemaVersion`, `id`, `name`, `version`, `description`, `author`,
`entryPoint`, `runtime`, `lanctl.minimumVersion`, `lanctl.maximumVersion`,
`permissions`, `capabilities` y `depends`.

Runtimes:
- `isolated`: solo manifiestos y extensiones declarativas; no ejecuta Python.
- `trusted`: ejecuta `activate(api)` y necesita `--trust`.

Capacidades reconocidas:
`plugin`, `theme`, `language`, `settings`, `automation`, `network`, `analysis`,
`ui`, `security`, `config`, `commands`, `protocol`, `scanner`,
`device-adapter`, `parser`, `exporter`, `project-handler`, `physical-model`, `icon`.

## Extensiones api/api.map

Cada elemento tiene `id`, `type` y `specification`. Tipos del registro común:
`command`, `theme`, `language`, `settings`, `automation`, `network`, `analysis`,
`ui-panel`, `ui-action`, `security`, `config`, `protocol`, `scanner`,
`device-adapter`, `parser`, `exporter`, `project-handler`, `physical-model`, `icon`.

Comando declarativo seguro:
```json
{"id":"example.summary","type":"command","specification":{"name":"summary","aliases":[],"help":"Resumen","action":"inventory.summary"}}
```
Acciones declarativas incluidas: `inventory.summary`. Las acciones desconocidas
se rechazan; un LCP no puede inyectar una función arbitraria mediante JSON.

Idioma:
```json
{"id":"example.language.ca","type":"language","specification":{"file":"assets/lang/catala.lang"}}
```

## Permisos

`events.listen`, `events.emit`, `events.register`, `functions.call`,
`functions.register`, `command.register`, `theme.register`, `language.register`,
`settings.register`, `automation.register`, `network.register`,
`analysis.register`, `ui-panel.register`, `ui-action.register`,
`security.register`, `config.register`, `protocol.register`, `scanner.register`,
`device-adapter.register`, `parser.register`, `exporter.register`,
`project-handler.register`, `physical-model.register`, `icon.register`.

El acceso a red, credenciales, proyectos o dispositivos debe solicitar además
el permiso específico definido por la API que lo exponga. Las contraseñas no
se entregan directamente al plugin.

## Eventos y contratos

Formato: `LANCTL.<Categoría>.<Grupo>.<Evento>` para core y
`<Plugin>.<Categoría>.<Grupo>.<Evento>` para plugins.

Core inicial:
- `LANCTL.Core.Lifecycle.Startup|Shutdown` -> `LifecycleEvent`
- `LANCTL.Project.File.Open|Save|Reload|Close` -> `ProjectFileEvent`
- `LANCTL.Network.Scan.BeforeStart|Begin|End` -> `NetworkScanEvent`
- `LANCTL.Device.Remote.Connect|Disconnect` -> `DeviceRemoteEvent`

Todos heredan `EventContract` y contienen `EventMetadata`: `event_id`,
`event_version`, `source`, `timestamp`, `correlation_id`.

Tipos de `events.schema`: `string`, `integer`, `number`, `boolean`, `datetime`,
`object`, `array`; añade `?` para opcional. Ejemplo:
```json
{"events":{"Example.Network.Scan.Done":{"version":1,"arguments":{"scan_id":"string","note":"string?"}}}}
```

Hook trusted (`api/hooks/scan.hook`):
```json
{"event":"LANCTL.Network.Scan.Begin","handler":"on_scan","version":1,"priority":100}
```
El handler recibe la instancia completa del contrato. Los hooks cancelables
devuelven `HookDecision(allowed=False, reason="...")`.

## API trusted

`activate(api)` recibe `PluginApi`:
- `api.require(PERMISSION)`
- `api.log(action, target="-", result="OK", detail="")`
- `api.events.subscribe(...)`, `emit(...)`, `register(...)`
- `api.functions.register(...)`, `call(...)`
- `api.extensions.register(id, type, specification)`

Las funciones públicas deben devolver una dataclass de contrato, normalmente
`FunctionResult(success, code, message, data)`, nunca un diccionario suelto.

## Registro y seguridad

Cada acción escribe: `PLUGIN id=... action=... target=... result=... detail=...`.
El namespace `LANCTL.*` está reservado. La instalación queda desactivada. Los
plugins trusted requieren confianza explícita. Inicia con `pluginSafeMode=true`
para impedir la carga durante recuperación.

## Plugin de ejemplo incluido

`lanctl.example.network-summary` registra:
```bat
lanctl network-summary
lanctl netsummary
```
Es aislado, declarativo, no accede a red y solo lee el inventario local.
"""


def bootstrap_builtin_plugins(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    readme = root / "readme.md"
    if not readme.exists() or readme.read_text(encoding="utf-8") != PLUGIN_README:
        readme.write_text(PLUGIN_README, encoding="utf-8")
    plugin = root / EXAMPLE_PLUGIN_ID
    info = plugin / "plugin.info"
    api_map = plugin / "api/api.map"
    api_map.parent.mkdir(parents=True, exist_ok=True)
    info.write_text(json.dumps(EXAMPLE_MANIFEST, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    api_map.write_text(json.dumps(EXAMPLE_API_MAP, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
