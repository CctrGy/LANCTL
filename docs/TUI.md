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
| `Esc` | Cerrar modal o iniciar el cierre seguro |

En Settings, `←/→` cambia de sección, `↑/↓` selecciona una variable, `Tab`
entra o sale de edición y `Ctrl+S` valida y guarda. `Esc` cancela primero la
edición activa y, al pulsarlo de nuevo, cierra la ventana.

Si la salida queda deformada, amplía la terminal, evita fuentes que no respeten
el ancho de los caracteres y vuelve a abrir el TUI. Para una captura limpia se
recomienda Windows Terminal con UTF-8.
