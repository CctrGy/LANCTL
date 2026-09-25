# Integración de experimental — 2026-09-25

## Procedencia

- Repositorio: https://github.com/CctrGy/LANCTL
- Punto local inicial: `9ec9c4a` (`main`, limpio).
- Rama revisada: `origin/experimental`, commit `2f2795c`.
- Incluye `1a1e2ce` (corrección del enlace de documentación en README).
- Integración local mediante fast-forward, sin sobrescribir cambios locales.

## Cambios incorporados

LANWIRE añade perfiles de prefijos, creación explícita de IDF, identificadores
de 2–5 letras/dígitos, plantillas mixtas de puertos, compatibilidad de medios,
vista de topología, navegación entre cables/equipos y edición desde el TUI.
La persistencia actualiza referencias al renombrar puertos y limpia conexiones
al eliminar elementos, con escrituras transaccionales. La inicialización de
LANWIRE puede clasificar registros antiguos FB/WL/WE: conviene respaldar bases
reales antes de abrirlas con esta versión.

LANIP añade edición desde F2, ciclo de vistas con Tab, un IDF físico separado
del identificador interno y resolución de nombres en el perfil normal.
Esta última puede cambiar la duración del descubrimiento.

El bus mantiene los nombres de eventos y endurece la validación de versiones
y propietarios de emisión. Los plugins que emitían contratos ajenos ahora
reciben un rechazo; escuchar eventos sigue siendo una operación diferente.

## Correcciones adicionales locales

- Permitir retirar un IDF aunque otros dispositivos también carezcan de IDF.
- Desactivar expansión retardada al pasar argumentos de `run.cmd`, para
  conservar signos de exclamación.
- Normalizar firmas AST del catálogo: Python 3.13+ omite listas vacías por
  defecto. Se conserva la representación de Python 3.10–3.12 para que los
  IDs no dependan de esa diferencia del intérprete.
- Aplicar el formato del proyecto y regenerar las referencias CLI/web y
  `errorList.txt` (1005 puntos).

## Verificación y alcance

Suite principal: 723 pruebas y 629 subpruebas correctas; las 21 pruebas legacy GUI
también pasan ejecutadas por separado. Tras añadir la regresión del AST,
15 pruebas dirigidas de catálogo, edición y referencia web correctas.
Catálogo idéntico comprobado con Python 3.10, 3.13 y 3.14.
Ruff, formato, referencias e higiene de Git correctos.

No se han abierto ni migrado deliberadamente proyectos reales para probar la
topología, ni realizado una validación visual interactiva de todas las pantallas.
No se han actualizado los ejecutables instalados, publicado releases ni hecho
push. Las correcciones posteriores al fast-forward quedan sin commit para revisión.
