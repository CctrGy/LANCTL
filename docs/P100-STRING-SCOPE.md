# P100 — Alcance del inventario de internacionalización

Revisión de fuentes locales del 27/10/2026. No es una migración de idiomas ni
una certificación de los ejecutables instalados. Incluye cambios locales
existentes; no se han modificado interfaces, catálogos ni datos del usuario.

## Entregables y reproducción

- `P100-STRING-INVENTORY.csv`: una fila por ocurrencia, con archivo, línea,
  columna, propietario, interfaz de origen, tipo, clasificación provisional,
  contexto, clave si está identificada, texto y SHA-256 de la fuente.
- `P100-STRING-FILES.json`: manifiesto de todos los archivos examinados,
  incluidos los que no aportan entradas; permite comprobar el alcance y cambios.
- `P100-STRING-SUMMARY.md`: recuentos por propietario/interfaz y clasificación.
- `../tools/generate_string_inventory.py`: regeneración determinista y modo
  `--check`, sin importar LANCTL ni leer su configuración local.

```sh
python3 tools/generate_string_inventory.py
python3 tools/generate_string_inventory.py --check
```

Los recuentos del resumen son ocurrencias, con repeticiones, claves, selectores,
valores internos y contenido técnico. No equivalen a claves nuevas que deban
crearse. El número de valores distintos tampoco equivale a mensajes distintos:
un mismo texto puede tener significados/contextos diferentes.

## Matriz de puntos de entrada y consumidores

Los ocho scripts declarados en `pyproject.toml` corresponden a seis launchers;
`als` reutiliza LANIP y `lanwre` reutiliza LANWIRE. No tienen catálogos propios.

| Launcher | CLI / entrada | TUI | GUI |
|---|---|---|---|
| LANCTL | `bootstrap/lanctl.py`, `apps/suite/interfaces.py` | Consola común `core/interactive_console.py`, `core/terminal_ui.py` | `apps/suite/gui.py`, `gui/suite.html`, `gui/suite.js`, ajustes compartidos |
| LANIP / als | `apps/ip/interfaces/cli/main.py`, `commands/`, terminales de infraestructura | `apps/ip/interfaces/tui/` | `apps/ip/interfaces/gui/desktop.py`, `gui/index.html`, módulos LANIP y diálogos compartidos |
| LANWIRE / lanwre | `apps/wire/cli/` | `apps/wire/tui/` | `apps/wire/gui_service.py`, plantilla común y `gui/wire-gui.js` |
| LANRACK | `apps/rack/cli.py` | Mismo módulo y consola común | Plantilla común, `gui/physical-gui.js`, editores físicos y módulos rack |
| LANACCESS | `apps/access/manager_cli.py` | Bucle `_tui_loop` del mismo módulo | `apps/access/gui_service.py` y plantilla común |
| LANMON | `bootstrap/lanmon.py`, `apps/monitor/commands.py`, `interfaces.py` | `interfaces.py`, `log_tui.py` y consola/visor de logs | `apps/monitor/gui_service.py`, plantilla común y `gui/monitor-support.js` |

Las rutas Python de la tabla son relativas a `src/lanctl/`. La plantilla común
es `gui/launcher.html` y `gui/launcher.js`, servida por
`apps/suite/launcher_gui.py`. Sus textos necesitan atribución a los consumidores,
no seis copias del mismo literal. `SHARED` en el inventario significa propiedad
compartida o atribución pendiente; no implica que todos los launchers consuman
cada texto. La terminal embebida muestra la salida del launcher invocado, además
de controles GUI propios; no debe traducir de nuevo la salida recibida.

## Capas transversales que entran en P100

- Parsers y ayuda: descripciones, epílogos, ayuda de opciones, errores de uso y
  formato común en `core/parser.py`; conservar nombres de comandos y opciones.
- Consolas/TUI: instrucciones, atajos, tablas, modales, formularios, paneles de
  ajustes/proyectos, estados, validaciones y cierre. Textos CLI reutilizados en
  TUI no deben contarse como implementaciones independientes.
- GUI: texto HTML, atributos accesibles y placeholders, plantillas JavaScript,
  mensajes RPC, contenido insertado dinámicamente, tooltips y pseudo-elementos
  CSS con `content`; incluir ajustes, remoto y primer escaneo.
- Servicios/Core: excepciones y mensajes retornados a varias interfaces,
  inventario, proyectos, permisos, credenciales, descubrimiento, monitorización,
  instalación/actualización y diagnóstico. Distinguir explicación de usuario
  de detalle técnico original antes de migrar cada caso.
- Plugins incluidos: seis directorios de `plugins-src`; metadatos, descripciones,
  acciones declarativas y mensajes de `main.exec` se inventarían con propietario
  propio. APIs/mapas/registros incluyen también contratos no traducibles.
- Distribución: scripts y fuentes Inno/Clink bajo `packaging` se incluyen como
  superficie adicional, separada de la interfaz de ejecución. El idioma del
  instalador y el idioma del programa tienen consumidores distintos.
- Prototipos: conservarlos identificados aparte; su existencia no acredita una
  pantalla disponible en distribución. Revisar su continuidad al migrar.

## Catálogos y situación encontrada

El inglés/español integrado tiene 67 claves por idioma. En el estado actual hay
además dos catálogos de 67 claves en `bundled/languages`, con manifiesto y
validación de hashes en `core/installation_languages.py`. Esto actualiza el
hallazgo anterior de P100 sobre ausencia de catálogo español distribuible; no
acredita traducción completa. El catálogo instalado local antiguo de 54 claves
no se incorpora al inventario reproducible porque es dato de usuario.

Mantener las claves actuales, localizar sus consumidores estáticos y dinámicos
(por ejemplo `LANCTL.INVENTORY.MANUAL.{key}`) y documentar su destino v2.
Los diccionarios Python y los archivos `.lang` duplican contenido de referencia:
la siguiente fase debe definir una fuente reproducible y validar sincronización.

## Interpretación y límites explícitos

La extracción Python utiliza AST, omite docstrings y conserva f-strings como
plantillas de fuente, incluidos sus parámetros. HTML conserva textos y atributos
con contexto de etiqueta. JSON conserva valores y su ruta lógica; ante valores
repetidos la línea señala su primera aparición textual, por lo que el contexto
JSON es la referencia desambiguadora. JavaScript/CSS y scripts de empaquetado
usan extracción léxica conservadora de comillas/plantillas: no sustituyen a un
parser de cada lenguaje. Bloques `script/style` embebidos se conservan enteros
para revisión; no se presentan como mensajes individuales ya clasificados.

No se recorren documentación, pruebas, herramientas auxiliares, referencias
web generadas, recursos binarios, paquetes externos, traducciones de librerías,
builds ni archivos locales. Se excluyen bases técnicas como el listado de
fabricantes MAC y recetas de desarrollo. Los textos producidos por dependencias,
SO, dispositivos y procesos se consideran salida externa que debe preservarse;
si una interfaz les añade una explicación propia, esa explicación sí entra.
El manifiesto permite detectar fuentes fuera de los tipos/rutas seleccionados.

`UI_CANDIDATE` es una prioridad de revisión, no aprobación de traducción.
`TECHNICAL_ERROR_REVIEW_PRESENTATION` exige seguir el error hasta su presentación.
`REVIEW` contiene claves internas, valores, selectores y también textos visibles;
no puede descartarse en bloque. En Python, clasificar un argumento de `print`
como candidato no convierte los datos técnicos impresos en texto traducible.
Los escapes léxicos se conservan como fuente, sin evaluar código.

## Trabajo necesario para cerrar el inventario funcional

1. Revisar las entradas y atribuir textos compartidos a sus consumidores reales;
   añadir pantalla/flujo, clave estable propuesta y decisión traducible/técnico
   con justificación. Revisar errores que viajan a través de RPC/consola.
2. Descomponer plantillas HTML/JS y código embebido, y seguir textos construidos
   por concatenación, parámetros y fuentes declarativas. Contrastar con rutas
   del frontend y permisos/estados que activan controles y mensajes.
3. Recorrer por launcher arranque/ayuda, proyecto vacío/con datos/sin proyecto,
   creación/edición/eliminación, ajustes, cancelaciones y fallos controlados;
   incluir primer uso, remoto, plugins y confirmaciones de cierre.
4. Validar esa matriz en CLI/TUI/GUI disponibles y Windows/Linux, registrar
   evidencia y comprobar que cada texto visible tiene fila y destino. Solo
   entonces declarar completo el inventario funcional y fijar el número de
   claves a migrar. Este barrido estático permite comenzar esa revisión, pero
   no demuestra por sí solo exhaustividad de pantallas o flujos.

Orden sugerido: infraestructura y mensajes comunes; LANCTL y LANIP; LANWIRE;
LANRACK/LANACCESS/LANMON y consumidores de plantilla común; plugins y
empaquetado; comprobación transversal. Migrar interfaz y servicio compartido
juntos cuando un mismo mensaje llegue a varios destinos.

## Mapa preliminar sin idioma

`P100-STRING-MAP.lang` utiliza `schemaVersion: 2`,
`documentType: LANCTL.P100.StringInventory`, `installable: false` y
`meta.code: null`. Es un mapa de trabajo, no un catálogo instalable.

La sección `LAUNCHERS` contiene los seis launchers y siempre los bloques
`CLI`, `TUI`, `GUI`, con pares directos `"identificador": "texto original"`.
No hay objetos de metadatos intercalados entre las cadenas. Se puede mover
cada par al destino revisado conservando su identificador provisional.

`PENDING_ASSIGNMENT` conserva las cadenas compartidas, mixtas CLI/TUI,
catálogos, prototipos, plugins e instaladores cuya atribución a una de las
18 secciones principales no está resuelta. No se duplican ni se asignan
arbitrariamente a un launcher. La agrupación actual es indicativa del archivo
de origen; todavía requiere revisión de consumidores y traducibilidad.

`P100-STRING-MAP-SOURCES.json` conserva por identificador las ubicaciones,
contexto, clasificación, clave existente, `targetKey`, `decision` y posición
inicial en el mapa. Al mover una cadena, esa posición inicial queda como
referencia histórica, no como ubicación vigente. Las decisiones y claves
propuestas se anotan en este auxiliar. Así se mantiene el mapa fácil de leer.

Los identificadores `P100.STRING.<hash>` se conservan respecto al mapa anterior:
no son claves públicas aprobadas y solo identifican ocurrencias de la fotografía
CSV utilizada. El contenido original puede incluir idiomas diferentes, código
y datos técnicos, que deben conservarse literalmente. Reutilizar claves públicas
existentes cuando corresponda y clasificar antes de migrar al sistema real.

Generación: `python3 tools/generate_string_map.py`; comprobación inicial:
`python3 tools/generate_string_map.py --check`. Se protegen ambos archivos
contra sobrescritura de modificaciones manuales. El generador admite migrar
automáticamente el mapa v1 únicamente si coincide con el CSV sin anotaciones.
Después de mover pares o anotar decisiones, `--check` detectará diferencias
esperadas: reconciliarlas explícitamente sin perder ese trabajo.
