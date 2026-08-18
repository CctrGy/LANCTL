# LANCTL Complement Platform (LCP) 1.0

## Política de compatibilidad 0.3

- LANCTL `0.3.x` escribe LCP con `schemaVersion: 1` y acepta paquetes creados
  por alphas, betas y versiones estables de la misma serie que mantengan ese
  esquema.
- Los campos desconocidos son aditivos y se ignoran; eliminar o cambiar el
  significado de un campo exige una nueva versión de esquema.
- Un esquema futuro se rechaza antes de instalar o ejecutar el paquete. No se
  intenta una conversión destructiva ni se sustituye el plugin ya instalado.
- Actualizar un plugin es transaccional: primero se verifica y extrae en un
  staging; si la sustitución falla se restaura la instalación anterior.
- No se garantiza que una versión antigua de LANCTL pueda abrir paquetes
  creados con un esquema futuro.

LANCTL utiliza `.lcp` como contenedor ZIP seguro para todos sus complementos.
Un mismo paquete puede aportar capacidades `plugin`, `theme`, `language`,
`settings`, `automation`, `network`, `analysis`, `ui`, `security`, `protocol`,
`scanner`, `parser`, `exporter`, `project-handler` o `project-save-mode`. CLI, TUI y la futura GUI
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

### Modos de guardado de proyectos

Un plugin puede añadir una política `SaveMode` declarativa con el permiso
`project-save-mode.register`:

```json
{
  "id": "example.save.after-scan-or-close",
  "type": "project-save-mode",
  "specification": {
    "mode": "example.afterScanOrClose",
    "triggers": ["scan", "close"],
    "description": "Guarda tras escanear o cerrar"
  }
}
```

Los únicos disparadores admitidos son `change`, `scan`, `close` y `timer`; el guardado
continúa ejecutándose de forma transaccional por el núcleo.

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

## Adaptadores de fabricante y comandos con función

Un plugin `trusted` puede enriquecer el análisis de una MAC registrando un
`device-adapter` con el rol `manufacturer-resolver`. La función recibe la MAC
normalizada y devuelve un `FunctionResult` cuyo `data` es el fabricante. Los
adaptadores activos se consultan antes de la base local integrada:

```json
{
  "id": "example.mac-vendor.resolver",
  "type": "device-adapter",
  "specification": {
    "role": "manufacturer-resolver",
    "function": "Example.Manufacturer.Resolve"
  }
}
```

Los comandos declarativos pueden usar `action: "function.call"` y declarar la
función mediante `function`. Los argumentos restantes de la CLI se entregan a
la función como una lista. La función debe pertenecer a un namespace no
reservado y el plugin necesita `command.register` y `functions.register`.

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
# Fachada Wake-on-LAN

Los plugins trusted pueden solicitar `network.udp` y usar exclusivamente
`api.network.send_wol(mac, broadcast, port, repeat, interval, interface)`.
La fachada valida MAC, IPv4, puerto y límites; no entrega sockets, credenciales
ni dispositivos internos al plugin. `lanctl.network.wol` registra la función
tipada `lanctl-network-wol.send` y una `ui-action` declarativa sin JavaScript.

Los plugins pueden solicitar `history.write`. Solo pueden emitir tipos bajo su
propio namespace mediante `api.history.write(...)`; no pueden falsificar tipos
reservados del núcleo, el actor ni el origen. Todos los detalles pasan por la
redacción central antes de escribirse en el VLF.
# Paneles y acciones de datos

`ui-panel` declara una plantilla permitida (`resource-browser`, `master-detail`, `table` o `form`), un `dataProvider` JSON y columnas con tipos visuales validados. `ui-action` declara una función del mismo propietario, placement, selección y confirmación. El core nunca interpreta HTML, JavaScript o CSS de plugins y elimina paneles/acciones al desactivar su propietario. Los contratos son JSON transportables y no dependen de pywebview.
