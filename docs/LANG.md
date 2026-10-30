# Idiomas de LANCTL

LANCTL utiliza catálogos JSON con extensión `.lang`. Las claves son contratos
estables, por ejemplo `LANCTL.CORE.APP.CANCELLED`, y no el texto original.

```json
{
  "schemaVersion": 2,
  "meta": {"code":"es","name":"Spanish","nativeName":"Español","region":"España","version":"2.0","author":"LANCTL"},
  "SHARED": {
    "LANCTL.CORE.APP.CANCELLED": "Operación cancelada.",
    "LANCTL.LANGUAGE.ERROR.NOT_FOUND": "Idioma no instalado: {language}"
  },
  "LAUNCHERS": {
    "LANCTL": {"CLI": {}, "TUI": {}, "GUI": {}},
    "LANIP": {"CLI": {}, "TUI": {}, "GUI": {}},
    "LANWIRE": {"CLI": {}, "TUI": {}, "GUI": {}},
    "LANRACK": {"CLI": {}, "TUI": {}, "GUI": {}},
    "LANACCESS": {"CLI": {}, "TUI": {}, "GUI": {}},
    "LANMON": {"CLI": {}, "TUI": {}, "GUI": {}}
  }
}
```

Los placeholders deben coincidir con el catálogo inglés. Una instalación nueva
genera únicamente `english.lang`; otros idiomas se instalan aparte.

```text
./data/lc/languajes/
├── english.lang
├── español.lang
└── languajes.json
```

Se conserva el nombre histórico `languajes`. `languajes.json` es un índice
generado por LANCTL y no debe editarse manualmente.

```bat
lanctl language list
lanctl language use es
lanctl language info es
lanctl language validate español.lang
lanctl language install español.lang
lanctl language export plantilla.lang
```

Las claves ausentes siempre usan inglés como fallback. Un LCP puede aportar un
catálogo declarando una extensión `language` cuyo `specification.file` apunte a
su `.lang`; requiere el permiso `language.register`.

Los módulos nuevos deben usar `t("CLAVE")` para todo texto visible.

## Catálogos oficiales incluidos en el instalador

`bundled/languages/` contiene los catálogos de distribución, distintos del
directorio mutable del usuario. `catalog.json` y
`packaging/inno/program-languages.iss` se generan con:

```sh
python tools/generate_installer_languages.py
python tools/generate_installer_languages.py --check
```

Para incorporar un idioma, añade su `.lang` con metadatos, código único y
placeholders compatibles y vuelve a generar esos dos archivos. No hace falta
editar una enumeración de idiomas en el asistente. La validación rechaza
catálogos incompatibles, códigos duplicados, enlaces y nombres no válidos.
El manifiesto asocia cada catálogo a su SHA-256; el servicio vuelve a comprobarlo
antes de instalar o seleccionar un idioma. El bundle siempre incluye inglés.

Setup usa `setup-defaults --language CODIGO` para el primer inicio. Durante
una actualización conserva la configuración salvo `--change-language`
explícito. Un catálogo personalizado ya instalado y válido se conserva. El
gestor de idiomas del primer arranque lee el mismo directorio e índice que
la instalación; el código no puede quedar seleccionado sin catálogo válido.

El asistente tiene traducciones propias en `packaging/inno/messages.iss`, con
las mismas claves para inglés y español. Sus mensajes estándar se obtienen de
los `.isl` oficiales de Inno Setup. Añadir otro idioma del asistente requiere
su entrada `[Languages]` y sus traducciones de mensajes personalizados; es
independiente de añadir un catálogo de idioma del programa.

## Contrato v2 y transición

El esquema usa un entero exacto, 1 o 2. No se aceptan `1.2`, `2.0`, cadenas,
booleanos ni versiones desconocidas. Los catálogos v1 con `strings` siguen
siendo válidos. Los v2 utilizan `SHARED` y `LAUNCHERS` en mayúsculas; cada
launcher admite CLI/TUI/GUI y opcionalmente SHARED. Se permiten subsecciones
para organizar pantallas. La clave pública identifica al texto con independencia
de su posición. Claves repetidas, incluidos duplicados entre secciones y
miembros JSON repetidos, se rechazan sin escoger una traducción arbitraria.

Los mapas `P100-STRING-MAP.lang` son inventarios con idioma nulo, no catálogos
instalables. Los IDs provisionales `P100.STRING.*` no deben usarse en producción.

La fuente bilingüe conserva las claves históricas en `shared/i18n.py` y las
cadenas de presentación nuevas en `shared/ui_messages.py`. Los archivos de
salida son reproducibles; no editar los catálogos oficiales generados a mano:

```sh
python tools/generate_language_catalogs.py
python tools/generate_installer_languages.py
python tools/generate_language_catalogs.py --check
python tools/generate_installer_languages.py --check
python tools/audit_language_usage.py
```

El primer comando genera los dos `.lang` y `gui/i18n-defaults.js`. El segundo
actualiza el manifiesto/hash del bundle y las opciones Inno. Los datos del
usuario no se regeneran. Las traducciones personalizadas v1/v2 existentes se
conservan, incluidas sus versiones de archivo. Las claves nuevas que no estén
en ellas usan fallback. Una traducción vacía también recurre al fallback.

## Consumidores y parámetros

Python utiliza `t("CLAVE", nombre=valor)` en el punto de presentación. Los
textos definidos como datos estáticos almacenan claves y se resuelven al
renderizar, no al importar el módulo. `language_context("en")` permite generar
referencias canónicas sin escribir preferencias ni alterar el idioma de otras
tareas. La selección CLI persiste en la configuración; reiniciar aplica el
idioma a todos los componentes. Los tres bootstrap GUI incluyen
`languageCatalog: {code, strings}`; el remoto lo recibe en su bootstrap
autorizado. No se añade un RPC de ejecución arbitraria.

El frontend carga `i18n-defaults.js` e `i18n.js` antes de sus scripts de interfaz.
`LanctlI18n.setCatalog(payload)` aplica el catálogo a los bindings explícitos.
Usar `data-i18n="CLAVE"` en nodos de texto aislados, y
`data-i18n-title`, `data-i18n-placeholder`, `data-i18n-aria-label` o
`data-i18n-alt` para atributos. Los nuevos nodos marcados se traducen mediante
observación del DOM, sin buscar ni sustituir texto arbitrario. Para etiquetas
creadas por JavaScript, `bindText(elemento, clave)` conserva el nodo textual
al añadir campos hijos. `t` devuelve texto; `html` escapa el resultado para
interpolaciones en HTML. Las funciones que generan botones/tablas escapan sus
etiquetas. Las traducciones nunca se evalúan como código.

Los placeholders son nombres simples `{device}`, `{path}`: ni atributos,
índices ni campos de formato anidados. Mantener el mismo conjunto en ambos
idiomas. Python admite conversiones y formatos simples; los consumidores web
actuales utilizan parámetros simples sin especificadores numéricos. Los
valores interpolados no se traducen. Para mensajes compartidos con web evitar
formatos que no estén implementados y probados en ambos consumidores.

El fallback de claves sigue catálogo seleccionado → idioma base instalado →
inglés instalado → inglés integrado. La GUI recibe esa misma combinación.
Los logs originales, trazas, IDs, claves técnicas, comandos y datos de usuario
quedan fuera de la traducción. Las dos claves técnicas históricas de ruta y
plantilla de log conservan su identidad, pero su valor efectivo se obtiene del
original integrado aunque un catálogo intente modificarlo.

## Alcance real de P100

La base v2 y una primera migración transversal están implementadas. La paridad
de los `.lang` indica completitud respecto al conjunto de claves registradas,
no cobertura total de todas las pantallas. Persisten literales y contenido
dinámico pendientes de revisar y migrar. Consultar `P100-PRELIMINARY-REVIEW.md`,
`P100-PRELIMINARY-REVIEW.json` y `P100-RESIDUAL-STRINGS.csv`. La revisión estética
y la certificación nativa Windows/Linux se gestionan después de la migración
funcional; no se declara cerrada P100 por generar estos catálogos.

## Presentación y diagnóstico durante P100

Las parejas fuente se mantienen en `src/lanctl/shared/ui_messages*.py` y se
cargan de forma diferida. `generate_language_catalogs.py` genera los catálogos
oficiales y el fallback JS; `generate_installer_languages.py` actualiza hashes.
`audit_language_usage.py` contrasta referencias, parámetros y candidatos residuales.

`TranslatedText` conserva el texto canónico para el logger y la etiqueta original
para identificadores de navegación. Los adaptadores de metadatos traducen al
presentar, sin cambiar claves, datos ni valores persistidos. Los errores técnicos
y salida externa se conservan. Los plugins externos deben declarar sus propios
textos/claves: no se traducen datos arbitrarios por coincidencia de palabras.
