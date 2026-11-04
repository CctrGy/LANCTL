# Revisión del almacenamiento de idiomas — 04/11/2026

## Alcance y resultado

Revisión de las fuentes y del empaquetado actual. Se inspeccionaron los recursos
del binario Linux local y se reprodujo la creación/selección de catálogos en
directorios temporales. No se ha inspeccionado un `.exe` Windows concreto ni se
ha cambiado el comportamiento de ejecución, la configuración o los idiomas del
usuario. El contenido previsto para Windows se deduce de `LANCTL.spec`.

La impresión del usuario es correcta: se distribuyen varios niveles de textos
completos y se crea además un catálogo inglés mutable. Hay redundancia, aunque
cada nivel nació con una finalidad: distribución sin conexión, respaldo y
compatibilidad con traducciones personalizadas.

## Estructura comprobada

| Nivel | Ubicación actual | Comportamiento |
| --- | --- | --- |
| Fuentes bilingües ejecutables | `src/lanctl/shared/i18n.py` y `ui_messages*.py` | Incluyen inglés/español; PyInstaller recopila los módulos de LANCTL. |
| Catálogos de distribución | `bundled/languages/english.lang`, `spanish.lang` y `catalog.json` | El mismo conjunto de recursos se incorpora a los siete ejecutables definidos en el spec. |
| Respaldo web | `gui/i18n-defaults.js` | Contiene inglés integrado para el frontend; también se empaqueta con los recursos GUI. |
| Catálogos mutables | Directorio de idiomas resuelto por `application_path` | Al inicializar, se escribe `english.lang` si falta; el idioma elegido se instala aparte. |
| Preferencia e índice | Configuración `language` y `languajes.json` generado | La preferencia usa un código de idioma; el índice registra selección y catálogos. |
| Idioma del instalador | Inno `.isl`/`messages.iss` y Linux `setup_messages.py` | Independiente del idioma seleccionado para LANCTL. |

`bundled_path` resuelve los recursos empaquetados mediante `_MEIPASS` en las
compilaciones one-file. Esa carpeta de extracción no es el almacén persistente
del usuario ni una carpeta compartida permanente entre ejecutables.

La ruta histórica `data/lc/languajes` se redirige a `config/languages` bajo la
raíz de datos. Sin embargo, la configuración también declara
`languagesDirectory = data/lc/languages`, mientras el gestor global se construye
con su constante histórica. Esta discrepancia debe resolverse al rediseñar;
no basta con cambiar el nombre de una carpeta en la documentación.

## Selección y respaldo

El valor inicial de configuración es `en`. El instalador puede elegir otro
código y conservar la elección anterior al actualizar. El inglés es el idioma
base de respaldo, no necesariamente el idioma que verá siempre el usuario.

La resolución de textos utiliza el catálogo seleccionado, su idioma base,
el inglés instalado y el inglés integrado, en ese orden. La GUI recibe una
combinación preparada por el backend; antes dispone de su respaldo JavaScript.
La inicialización crea el archivo inglés aunque se vaya a seleccionar español.

Incluir español en el ejecutable no equivale a instalarlo o seleccionarlo en
el directorio mutable. Las plantillas españolas de Python también intervienen
en `TranslatedText.source_text` y en el adaptador histórico `translate_label`.
Las inglesas se usan para registros canónicos y validación de placeholders.
Eliminar esas tablas sin migrar sus consumidores rompería otras funciones.

## Hallazgo de integridad independiente del diseño

En la instantánea revisada hay 2.514 claves por idioma. Los catálogos oficiales
y el fallback web pasan `generate_language_catalogs.py --check`, pero los hashes
de ambos `.lang` no coinciden con `bundled/languages/catalog.json`.
`generate_installer_languages.py --check` detecta el manifiesto obsoleto y
`available_languages()` rechaza el bundle con `Installation language checksum
mismatch`. No demuestra que un instalador anterior ya construido tenga el mismo
defecto; sí impide considerar verificado un nuevo build con estos recursos.

La instalación directa del catálogo español con `LanguageManager` en un
directorio temporal funciona y deja inglés/español con selección `es`.
El rechazo detectado corresponde al manifiesto de distribución, no a una
incapacidad del gestor para seleccionar español. Debe regenerarse y verificarse
el manifiesto al preparar la distribución; esta revisión no ha modificado
generados que pueden estar siendo actualizados por otras tareas.

## Propuesta de rediseño para evaluar

**Concreción posterior del usuario:** P121 de [BACKLOG.md](BACKLOG.md) propone
un archivo `.lang` en formato ZIP por idioma, con `info.json`, `shared.json` y
un JSON por launcher. Esa es la estructura solicitada para evaluar; los puntos
siguientes recogen los objetivos de separación y respaldo del análisis inicial,
no una decisión de sustituir el paquete por carpetas de idioma independientes.
La propuesta sigue pendiente de implementación.


1. Mantener los catálogos `.lang` como recursos de datos versionados y una única
   fuente de traducciones. Separar las fuentes de generación del código que
   se incorpora al runtime; no compilar innecesariamente todas las parejas
   bilingües dentro de cada launcher.
2. Distribuir un directorio de idiomas oficiales de solo lectura, compartido por
   los ejecutables instalados. El instalador lleva los idiomas que permite
   seleccionar sin conexión; la instalación mantiene al menos el idioma elegido
   y el inglés de respaldo. En portable, mantener recursos junto al programa y
   datos mutables separados. Si se conserva one-file, definir expresamente qué
   recursos mínimos siguen integrados y cómo se localizan los externos.
3. Reservar el directorio del usuario para idiomas añadidos, personalizaciones
   y el índice/preferencia. No copiar automáticamente un inglés oficial completo
   por cada usuario cuando puede leerse del directorio de distribución.
4. Conservar un respaldo mínimo integrado para avisar de recursos ausentes,
   inválidos o incompatibles. El inglés completo oficial puede ser un recurso
   compartido; reducir el respaldo requiere mantener diagnósticos y recuperación
   cuando todavía no se puede cargar ese archivo.
5. Dar a CLI/TUI/GUI un único resolvedor y precedencias documentadas. En la GUI,
   consumir el catálogo resuelto por el backend y evitar duplicar todo el inglés
   en JavaScript si ya está disponible, conservando los avisos mínimos previos
   al bootstrap. Una personalización parcial debe poder recurrir al catálogo
   oficial de su propio idioma antes de caer al inglés.
6. Mantener separados el idioma predeterminado de una instalación nueva, la
   elección del usuario y el idioma de respaldo. Migrar el adaptador de etiquetas
   antiguas a claves explícitas, conservar registros canónicos y generar los
   metadatos de claves/placeholders sin depender de traducciones completas
   compiladas.

La propuesta no está implementada. Antes de aplicarla hay que ajustar los
generadores, reglas de autoría, rutas, empaquetado e instaladores como un conjunto;
conservar claves, catálogos v1/v2 y personalizaciones existentes; y verificar
ausencia/corrupción de recursos, actualizaciones sin conexión, ámbitos usuario/
servicio, todos los launchers y las plataformas admitidas. La transición debe
coordinarse con P100 y P105/P106.

La motivación principal es claridad y mantenimiento. En esta instantánea los
dos `.lang` suman aproximadamente 428 KiB y el fallback web unos 196 KiB,
sin contar tablas Python ni compresión. Son tamaños de fuentes medidos, no
ahorros de binarios: no justifican atribuirles el tamaño completo de los
instaladores ni prometer una reducción sin compilar y medir.
