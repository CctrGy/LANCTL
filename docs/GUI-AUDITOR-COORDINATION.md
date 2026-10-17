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

Las diez regresiones de `tests/test_gui_support.py` comprueban persistencia y
sincronización, origen de errores, redacción y revisión de reportes, consulta
asíncrona de versiones, enlaces con navegador explícito, edición compartida de
racks y confirmación previa al primer escaneo. Las 33 regresiones de GUI,
topología/CPD y skins pasan con navegador Edge real. Los cuatro launchers
especializados abren y cierran correctamente mediante el host nativo.

La comprobación integral y el empaquetado final se registran después de que
AUDITOR estabilice los servicios. P34 (aislamiento/revocación completa), P50
(puente externo con contexto y autenticación), el enlace a interfaz de sondeo
de P47 y las certificaciones externas no se consideran terminados por estas
pruebas visuales.
