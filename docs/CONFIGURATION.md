# Configuración de LANCTL

LANCTL conserva una única configuración JSON con esquema versionado. Desde el
esquema 2, las opciones se agrupan por responsabilidad en vez de compartir un
espacio plano de claves.

```text
schemaVersion
├── storage          Recursos globales y secretos
├── logging          Registro y retención
├── projects         Proyecto activo, guardado y workspace
├── plugins          Instalación, registro y almacenamiento
├── localization     Idioma y catálogos
├── network          Parámetros de la LAN
├── ip               Descubrimiento e inventario lógico
├── tui              Atajos y botones visibles de LANIP
├── wol              Wake-on-LAN
├── access           Acceso local y remoto
└── monitor          Política de monitorización
```

## Bases de datos por proyecto

Los inventarios y bases operativas pertenecen al workspace del proyecto. Una
instalación nueva crea un workspace inicial llamado `default`:

```text
projects/workspaces/default/
├── database/
│   ├── devices.json
│   └── groups.json
├── monitoring/
│   ├── monitor.db
│   ├── sessions.json
│   ├── incidents.json
│   ├── profiles.json
│   └── assignments.json
└── physical/
    └── idf.db
```

Al activar otro proyecto, LANCTL cambia las rutas efectivas a su workspace sin
convertir esas bases en recursos globales.

## Compatibilidad y migración

Los archivos planos anteriores se convierten en memoria y se escriben como
`schemaVersion: 2` en el siguiente guardado. Las rutas existentes se conservan:
la conversión del formato no mueve ni elimina bases de datos reales.

Durante la transición, la API de configuración mantiene alias como `database`,
`workers` o `monitorDatabase` para plugins y componentes antiguos. El archivo en
disco siempre se guarda agrupado. También se admiten borradores tempranos del
esquema 2 que todavía situaban las bases bajo `storage` o `monitor.storage`.

Las escrituras usan bloqueo interproceso, archivo temporal y reemplazo atómico.
Un lector nunca observa un JSON parcialmente escrito.

## Teclado del TUI

La sección `tui.keyBindings` relaciona nombres de acciones estables con teclas
semánticas como `F5`, `CTRL_S` o `CTRL_J`. `tui.footerButtons` contiene las
acciones cuyas ayudas deben renderizarse en la última línea. Los valores pueden
editarse en `SETTINGS / MENU[TECLADO]` o mediante `settings --tui-key` y
`settings --tui-footer-button`.

Un valor JSON `null` representa una acción asignable sin atajo. SETTINGS lo
muestra como `None`; asignarle una tecla la activa y devolverla a `None` vuelve
a desactivarla. Las acciones opcionales no forman parte de `footerButtons` por
defecto.

La barra inferior muestra por defecto únicamente Ayuda, Info, Ping, Actualizar,
Plugins, Proyectos, Settings y Seleccionar. Ocultar el resto de ayudas no
desactiva sus atajos; pueden volver a mostrarse desde `SETTINGS / TECLADO`.
