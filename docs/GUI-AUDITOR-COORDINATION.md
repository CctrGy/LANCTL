# Integración de pendientes GUI y AUDITOR — 17/10/2026

El usuario solicita completar los pendientes de interfaz y encarga a AUDITOR
los cambios internos. El trabajo continúa en la rama existente experimental-gui,
sin publicar, instalar ni modificar la versión durante la integración.

## Propiedad de los cambios

- GUI-DESIGN: `gui/*`, adaptadores `apps/suite/gui.py`, `launcher_gui.py` y
  `apps/ip/interfaces/gui/desktop.py`; pruebas de integración de interfaces.
- AUDITOR: servicios y modelos compartidos, CLI/TUI, permisos, instaladores,
  comprobación de versiones, diagnóstico, transporte de actividad y dimensiones.
- Contratos de AUDITOR: `.tool-reports/gui-auditor-sync.json` (informe local,
  excluido de Git). Indicar firmas, payloads, archivos, comprobaciones y bloqueos.
- Los cambios de ambos se integran antes de ejecutar la suite completa y una
  única compilación final. Cada responsable ejecuta regresiones focalizadas.

## Dependencias

1. P54: enlaces oficiales compartidos; botones GUI con apertura de navegador
   mediante servicio, sin shell.
2. P34/P35: estado de permisos coherente, preferencias visuales validadas,
   cinco temas con previsualización y aplicación persistente.
3. P49/P53: visor de registros y transporte de actividad antes de sustituir
   el visor local de LANCTL. Conservar origen, proyecto, sesión y timestamps.
4. P52: preparación y redacción en LANMON, edición y revisión visual antes
   de abrir GitHub; nunca publicar automáticamente.
5. P51: consulta de actualizaciones en segundo plano y manual, estado visible,
   recordar después y enlace explícito sin descargar ni ejecutar instaladores.
6. Dimensiones de racks: validación compartida 4–52 U y ancho 10/19/21/23
   pulgadas; LANRACK edita y LANWIRE muestra el mismo registro.
7. P45–P48 y P32: integración del instalador y comprobaciones de distribución.

El backlog contiene dos entradas P66. En esta coordinación se identifican por
su título: «Frentes de equipos» (completada) y «Dimensiones de armarios rack»
(pendiente). No se reescriben identificadores públicos ni resultados anteriores.

## Requisitos que deben conservarse

Los puertos de los frentes de LANRACK son exclusivamente decorativos. Las
operaciones siguen en las ventanas de datos. Ninguna modificación visual
concede permisos de plugins, inventa firmas o sustituye la validación del Core.
Los cambios no deben perder conexiones, pertenencia a rack/CPD o datos del
proyecto. Las verificaciones externas no disponibles se documentan como tales.

## Integración de interfaz comprobada

Se incorporan los adaptadores `apps/suite/gui_support.py` y las extensiones
`app-preferences`, `app-support`, `monitor-support`, `rack-dimensions` y
`first-scan`. Usan los contratos internos entregados por AUDITOR, sin duplicar
la validación de preferencias, dimensiones o diagnósticos.

Las trece regresiones de `tests/test_gui_support.py` comprueban persistencia y
sincronización, origen de errores, redacción y revisión de reportes, consulta
asíncrona de versiones, enlaces con navegador explícito, edición compartida de
racks y confirmación previa al primer escaneo. Incluyen el reintento tras error,
el envío real de interfaz/CIDR al parser y el estado de reinicio/limpieza de
plugins, que impide ofrecer acciones no disponibles. Las regresiones de GUI,
topología/CPD y skins pasan con navegador Edge real. Los cuatro launchers
especializados abren y cierran correctamente mediante el host nativo.

La comprobación integral y el empaquetado final se registran después de que
AUDITOR estabilice los servicios. P34 (aislamiento/revocación completa), P50
(puente externo con contexto y autenticación), los transportes distintos de
ICMP/ARP de P47 y las certificaciones externas no se consideran terminados por
estas pruebas visuales.

## Corte final de fuentes

AUDITOR valida el corte integrado con Coverage 7.16.2: 1.212 pruebas y 645
subpruebas aprobadas en 185,61 s; cobertura de líneas/ramas 69,4720 %, sobre
el umbral del 60 %. La omisión corresponde al IPC POSIX en Windows. Las 21
pruebas GUI heredadas, excluidas por el selector habitual, pasan por separado:
1.233 pruebas aprobadas en total. Las trece regresiones de controles GUI
incluyen la conservación de la solicitud del primer escaneo tras error.

Antes de compilar se congelan 386 entradas de construcción, con hashes en
`.tool-reports/gui-package-freeze.json`. Las evidencias de distribución se
añaden tras comprobar recursos, versiones y cierre nativo de los binarios.
P69–P73 son anotaciones nuevas incorporadas desde HELP durante el ciclo y se
conservan pendientes; no se presentan como implementadas en este corte.

## Artefactos locales verificados

Compilados los seis ejecutables `0.3.4-alpha.1` sin cambios en las 386 entradas
congeladas. Cada archivo contiene los 29 recursos actuales de GUI/catálogo y
los 16 módulos compartidos comprobados, incluidos origen de red y estado de
plugins. Las seis ventanas pasan arranque nativo, icono, registro IPC y cierre
mediante `WM_CLOSE`; LANIP espera además a completar su inventario inicial.
Las pruebas usan almacenes y carpeta de proyectos temporales.

Inno Setup termina correctamente y genera
`dist/gui-current/LANCTL-0.3.4-alpha.1-gui-setup.exe` (135.487.663 bytes).
SHA-256:
`5401cb5a085c4cf8fa2b86dbb9270e72f6a45ff0cfdfbdbf1c4ce113626bde3a`.
Es un instalador experimental local; no se ha instalado ni publicado.
Compilar y ejecutar los binarios no certifica instalación/actualización en una
máquina limpia ni los entornos externos que AUDITOR sigue comprobando.

## Reapertura P45: imágenes de los temas

El reporte visual identifica que el Setup anterior solo mostraba `TPanel`
con fondo/acento y una leyenda de poco contraste: no contenía imágenes.
Se reemplaza por `TBitmapImage`, cinco BMP versionados con capturas de Inicio
y las paletas reales del Core, extracción temporal y cambio de archivo al
seleccionar tema. Se amplía la página y se distribuyen opciones e imagen en
dos columnas, manteniendo la proporción 8:5. El generador usa datos sintéticos.

Pasan 16 pruebas de distribución/recursos y Ruff; Inno compila correctamente.
El instalador actualizado ocupa 135.659.290 bytes y su SHA-256 es
`dcb5bd5a50fdb7167af7550cfc76eec4982194e726d044627270919f18d96ce5`.
Los seis ejecutables de aplicación conservan la compilación verificada previa.
El usuario abrió el Setup actualizado, aceptó manualmente UAC y confirmó que
las cinco vistas previas cambian y se ven completas: «Sí, las cinco se ven
bien». La herramienta no pudo capturar la ventana elevada, por lo que se
registra esa revisión humana, sin atribuirla a una captura automatizada.
P45 queda comprobada. La siguiente compilación incluirá además la corrección
posterior de registro Clink repetido (P48) entregada por AUDITOR.
