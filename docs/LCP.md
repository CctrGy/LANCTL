# LANCTL Complement Platform (LCP) 1.0

LANCTL utiliza `.lcp` como contenedor ZIP seguro para todos sus complementos.
Un mismo paquete puede aportar capacidades `plugin`, `theme`, `language`,
`settings`, `automation`, `network`, `analysis`, `ui`, `security`, `protocol`,
`scanner`, `parser`, `exporter` o `project-handler`. CLI, TUI y la futura GUI
consumen el mismo registro de extensiones.

Los plugins también pueden aportar recursos gráficos `icon` de 125×125 para
la futura GUI mediante el permiso `icon.register`.

## Estructura

```text
Complemento.lcp
├── plugin.info
├── main.exec
├── modules/
├── api/
│   ├── api.map
│   ├── events.schema
│   ├── events.registry
│   └── hooks/
├── assets/
├── config/
└── meta/
    ├── version
    ├── created
    ├── checksum
    └── signature       (opcional)
```

`plugin.info` es JSON y declara identidad, compatibilidad, runtime,
capacidades, permisos y dependencias. `api/api.map` registra extensiones
declarativas sin ejecutar código:

```json
{"extensions":[{"id":"example.theme.dark","type":"theme","specification":{"palette":"dark"}}]}
```

### Temas de la GUI

Los temas son extensiones declarativas `theme` con permiso `theme.register`.
No pueden incluir ni ejecutar CSS o JavaScript. La especificación contiene
`tokens` globales y ajustes opcionales para identificadores estables:

```json
{
  "id": "example.theme.dark",
  "type": "theme",
  "specification": {
    "tokens": {"color.accent": "#25a9e8", "radius.panel": "10px"},
    "components": {
      "lanctl.primary-action": {"color.accent": "#25a9e8"}
    }
  }
}
```

El core valida nombres, valores e identificadores antes de registrarlos. Los
colores solo admiten hexadecimal y las medidas admiten `px` o `rem`, evitando
la inyección de CSS arbitrario. El HTML enlaza el mismo contrato mediante
`data-component-id="lanctl.*"`.

## Runtimes y confianza

- `isolated`: carga manifiestos y extensiones declarativas. No ejecuta
  `main.exec` dentro de LANCTL.
- `trusted`: ejecuta `activate(api)` dentro del proceso y exige
  `plugin enable ID --trust`.

Los permisos no convierten Python in-process en un sandbox; `trusted` debe
reservarse para código conocido.

## Comandos

```bat
lanctl plugin pack Directorio MiPlugin.lcp
lanctl plugin verify MiPlugin.lcp
lanctl plugin install MiPlugin.lcp
lanctl plugin permissions example.plugin
lanctl plugin enable example.plugin --grant-all
lanctl plugin enable example.plugin --grant-all --trust
lanctl plugin list
lanctl plugin info example.plugin
lanctl plugin extensions
lanctl plugin reload example.plugin
lanctl plugin disable example.plugin
lanctl plugin uninstall example.plugin
```

La instalación nunca activa el paquete automáticamente.

## Complemento integrado de ejemplo

Las instalaciones nuevas incluyen `lanctl.example.network-summary`, un plugin
aislado y declarativo que demuestra el registro seguro de comandos:

```bat
lanctl network-summary
lanctl netsummary
```

Resume el inventario local, CNF, grupos y protocolos sin escanear ni conectarse
a ningún dispositivo. El manual completo para autores se genera en
`data/lc/plugins/readme.md`.

## Eventos y contratos

Los identificadores contienen cuatro niveles, por ejemplo
`LANCTL.Network.Scan.Begin` o `Example.Network.Scan.Completed`. Los contratos
son dataclasses inmutables y contienen metadatos con versión, fuente, fecha y
`correlation_id`. Los plugins no pueden apropiarse del namespace `LANCTL`.

El core registra eventos de ciclo de vida, proyectos, escaneo y conexiones.
`LANCTL.Network.Scan.BeforeStart` es cancelable mediante `HookDecision`. Una
excepción de un suscriptor se aísla y audita sin detener el core.

Los paquetes `trusted` pueden declarar hooks JSON en `api/hooks/*.hook`:

```json
{"event":"LANCTL.Network.Scan.Begin","handler":"on_scan_begin","priority":100}
```

El handler debe existir en `main.exec` y el plugin necesita `events.listen`.

## Auditoría y VLF

Toda acción usa el log diario normal y, si existe, el proyecto VLF activo:

```text
21:34:08 PLUGIN id=example.plugin action=EVENT HANDLE target=LANCTL.Network.Scan.Begin result=OK
21:34:09 PLUGIN id=example.plugin action=ENABLE target=1.0.0 result=ERROR detail=...
```

El código no se incrusta en el VLF. El proyecto incorpora
`plugins/registry.json` y puede conservar namespaces `plugins/<id>/`.

La configuración `pluginSafeMode: true` impide activar complementos durante
el arranque para permitir recuperación ante fallos.
