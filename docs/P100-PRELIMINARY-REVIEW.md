# P100 — Revisión preliminar de la migración de idiomas

27/10/2026. Se ha ampliado la migración funcional de los seis launchers,
sus interfaces existentes y los componentes compartidos. Los catálogos inglés
y español tienen **2.470 claves cada uno**. La estética se revisará después.
P100 conserva pendiente la certificación de recorridos e instalables nativos
Windows/Linux; la auditoría estática no demuestra por sí sola todos los estados
posibles del programa ni los textos de plugins externos.

## Código y consumidores

- Se mantiene el contrato v2 (`SHARED` y `LAUNCHERS`, CLI/TUI/GUI), el lector v1,
  los IDs históricos y el fallback seleccionado/base/inglés.
- Se migran ayudas de parsers y subcomandos, preguntas interactivas, consola,
  estados y resúmenes, ayuda y formularios TUI, etiquetas y confirmaciones GUI,
  configuración, metadatos visibles de plugins e informes HTML de demostración.
- Los módulos `shared/ui_messages*.py` contienen las parejas de textos fuente;
  los generadores producen ambos `.lang`, fallback JS y hashes de instalación.
  Los diccionarios se cargan al solicitar traducciones, evitando cargar el
  catálogo completo al importar utilidades en workers técnicos limitados.
- Los metadatos de dominio conservan IDs y valores originales; adaptadores
  `translate_label`/`translate_specification` traducen solo campos de presentación.
  Un plugin externo debe proporcionar sus claves/textos: su contenido arbitrario
  no puede traducirse automáticamente mediante el catálogo de LANCTL.
- Las cadenas con parámetros mantienen evaluación y formato. Los bindings DOM
  explícitos conservan parámetros y nodos hijos; los textos insertados en HTML
  se escapan. Los mapas GUI se consultan al renderizar tras recibir el idioma.
- `TranslatedText` conserva texto canónico inglés y metadatos originales. La
  consola muestra el idioma elegido y el logger recibe el texto canónico;
  los registros técnicos originales, excepciones y salida externa se preservan.
  Copia profunda/pickle conservan este contrato.
- La navegación TUI usa identificadores originales y traduce etiquetas al pintar;
  no depende de comparar pestañas con el idioma visible.

## Contraste inglés/español

`tools/audit_language_usage.py` comprueba 344 archivos fuente, 2.893 referencias
explícitas y 2.200 claves referenciadas estáticamente. El resto incluye claves
históricas y consumidores dinámicos declarados. Ambos catálogos tienen las mismas
claves y parámetros, sin referencias explícitas inexistentes. Se conservan las
exclusiones técnicas protegidas, los catálogos personalizados y la compatibilidad
v1. El inventario inicial de 31.902 ocurrencias sigue siendo una fotografía:
no son 31.902 mensajes traducibles independientes.

El CSV residual registra contexto, hash y disposición de cada candidato. Tras
revisar los textos pendientes identificados, quedan 397 candidatos explicados:
21 vistas de diseño, 37 bindings explícitos, 198 expresiones/datos/esquemas,
13 diagnósticos originales, 14 claves de esquema, 109 identificadores/símbolos
y 5 metadatos traducidos al presentar. No hay candidatos sin clasificar en esta
pasada. Estas reglas conservadoras y la inspección semántica local tienen límites:
no constituyen una prueba matemática de ausencia de literales en todas las rutas.

Fuentes reproducibles: `P100-PRELIMINARY-REVIEW.json` y
`P100-RESIDUAL-STRINGS.csv`. Las copias históricas `P100-STRING-INVENTORY.csv`
y `P100-STRING-MAP.lang` mantienen sus IDs y no se han regenerado.

## Validación

La ejecución final congelada pasa con **1.673 pruebas y 1.008 subpruebas**,
94 omisiones y 21 deselecciones, en 79,74 s, sin avisos. En una ejecución
anterior se observó un aviso de hilo en la prueba que
simula un fallo de terminación de plugins (`OSError: termination unavailable`);
no se ha ocultado ni modificado ese escenario técnico ajeno a la traducción.
Las pruebas finales seleccionadas de Chromium pasan **15 casos**: bindings y
conservación de datos/parámetros en inglés/español, configuración, inventario/terminal
y las cuatro variantes de sincronización de proyecto de LANIP.

El barrido AST adicional de JavaScript revisó también literales concatenados,
mapas de etiquetas y plantillas: se incorporaron confirmaciones, tooltips, títulos
y fragmentos que no recoge el auditor Python/HTML. La auditoría general conserva
expresamente esa limitación; no equivale a un parser JavaScript completo.

Las pruebas usan datos temporales, `PYTHONPATH=src` y `MALLOC_ARENA_MAX=2`:
el límite nativo de memoria de workers puede impedir crear hilos con el número
predeterminado de arenas de glibc. No se han relajado los límites del runtime.
No se han realizado escaneos reales ni reemplazado los idiomas personales.

## Pendiente de certificación

Recorrer los flujos completos de los seis launchers en instalaciones Windows y
Linux, incluidos plugins/terminales dependientes del sistema; revisar la estética
y compilar/certificar los instalables. No se ha publicado ninguna distribución.

La ampliación a las pruebas opcionales antiguas encontró Microsoft Edge ausente
(`BrowserType.launch: Chromium distribution msedge is not found`). Ese conjunto
no se declara superado. También localizó una expectativa de idioma fija y una
regresión real en fechas relativas (`returnwindow`); se corrigieron y se añadió
la espera del contenido de inventario en las pruebas de sincronización. Las cuatro variantes de cambio de proyecto pasan con Chromium.

Ruff no encuentra infracciones. La comprobación de formato pasa para 483 archivos;
`tools/complete_run.py` y `tests/test_run_completion.py` tienen diferencias de
formato previas, ajenas a P100, y se conservan. Los generadores de catálogos,
hashes, catálogo de errores y referencias, la higiene y `git diff --check` se
comprueban separadamente.
