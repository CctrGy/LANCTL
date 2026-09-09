# Manual del TUI

Inicia la interfaz con `lanctl --tui`. También puede abrir directamente
`PLUGINS`, `PROJECTS` o `SETTINGS`. La pantalla se adapta automáticamente a
terminales estrechas; se recomienda un mínimo de 80×24 para la demostración.

## Teclas principales

| Tecla | Acción |
| --- | --- |
| `↑/↓` | Seleccionar elemento o desplazar una lista |
| `Enter` | Ejecutar el comando escrito o confirmar una selección |
| `F1` | Ayuda de comandos |
| `F2` | Identidad, clasificación, red, accesos y puertos |
| `F3` | Ping del elemento seleccionado |
| `F5` | Descubrimiento y actualización |
| `F7` | Plugin Manager |
| `F9` | Project Manager |
| `F12` | Settings |
| `Ctrl+H` | Historial de comandos |
| `Ctrl+F` | Preparar una búsqueda o filtro |
| `Ctrl+R` | Recargar el inventario guardado sin escanear la red |
| `Ctrl+E` | Preparar la edición del elemento seleccionado |
| `Ctrl+G` | Preparar la gestión de grupos |
| `Ctrl+P` | Abrir directamente la sección de puertos |
| `Ctrl+O` | Preparar la apertura de SSH, HTTP, Telnet u otro acceso |
| `Ctrl+S` | Guardar manualmente el proyecto activo |
| `Ctrl+D` | Consultar si existen cambios pendientes |
| `Ctrl+X` | Copiar la fila completa seleccionada como texto tabulado |
| `Ctrl+J` | Copiar `idf`, MAC, IP, CNF, alias, nombre, grupo y descripción como JSON |
| `Ctrl+L` | Limpiar la salida y devolver el foco al prompt |
| `Ctrl+Q` | Iniciar el cierre seguro |
| `Esc` | Cerrar modal o iniciar el cierre seguro |

En Settings, `←/→` cambia de sección, `↑/↓` selecciona una variable, `Tab`
entra o sale de edición y `Ctrl+S` valida y guarda. `Esc` cancela primero la
edición activa y, al pulsarlo de nuevo, cierra la ventana.

## Project Manager

`F9` abre un catálogo persistente respaldado por `data/lc/projects/projects.db`.
Los proyectos encontrados en la carpeta Documentos de LANCTL aparecen primero;
los proyectos registrados en otras ubicaciones se muestran después y conservan
su ruta aunque temporalmente no estén disponibles.

Dentro de la ventana, `Ctrl+N` crea y activa un proyecto nuevo, `Enter` activa la
selección, `Supr` elimina un proyecto tras exigir la confirmación `ELIMINAR` y
`Ctrl+R` vuelve a descubrir los archivos. El proyecto activo no se puede borrar:
primero debe activarse otro para mantener consistente su espacio de trabajo.

La consola permite encadenar propiedades del elemento seleccionado en cualquier
orden, sin repetir el selector:

```text
element -name HomeNAS -alias NAS -description "Almacenamiento principal" -cnf O -group ASSETS
```

La sección `TECLADO` usa una única tabla `CAMPO | TECLA/VALOR | VISIBLE`.
Cada acción ocupa una fila: `Tab` permite reasignarla a `F1`–`F12` o a los
controles admitidos, mientras `Enter` alterna `ON/OFF` para su representación
en la barra inferior. Dos acciones no pueden compartir tecla. Ocultar una fila
de la barra no desactiva su atajo.

## Acciones opcionales

Las siguientes acciones aparecen en el editor con tecla `None`. No están
activas ni ocupan espacio en la barra hasta que el usuario les asigne una tecla:

- Historial del elemento y escaneo individual.
- Filtros de activos, desconectados y todos los elementos.
- Acceso directo a SSH, terminal, credenciales y Wake-on-LAN.
- Copia aislada de IP o MAC.
- Estado completo del proyecto activo.

`None` también puede asignarse a una acción existente para desactivar su atajo.
Las teclas fundamentales de navegación, `Enter` y `Esc` permanecen disponibles
para evitar que una configuración incorrecta bloquee el uso del TUI.

Si la salida queda deformada, amplía la terminal, evita fuentes que no respeten
el ancho de los caracteres y vuelve a abrir el TUI. Para una captura limpia se
recomienda Windows Terminal con UTF-8.
