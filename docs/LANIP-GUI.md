# GUI de LANIP

Interfaz de escritorio sobre pywebview, HTML/CSS/JavaScript local y los servicios
existentes de LANIP. No instala un servidor web ni abre un puerto de acceso remoto.
La API remota anterior conserva `GuiApi`; el escritorio utiliza `DesktopApi`.

## Abrir desde el repositorio

```powershell
.venv\Scripts\python.exe -m pip install -e ".[gui]"
.venv\Scripts\python.exe lanip.py --gui
```

Con una instalación que incluya estos cambios: `lanip --gui` o
`lanctl lanip --gui`. CLI y TUI siguen funcionando de forma independiente.
Desde 0.3.3 se incluye en el Setup y ZIP portable de Windows. Las versiones
anteriores conservan sus binarios originales.

## Funciones

- Inventario IP/MAC con búsqueda local, filtros por estado/grupo, ordenación,
  columnas seleccionables y edición de alias, nombre, descripción, CNF e icono.
- Grupos: crear y añadir/retirar el elemento seleccionado, mediante el servicio
  transaccional compartido; se mantienen las protecciones de elementos básicos.
- Escaneo rápido, normal y preciso, progreso consultable y cancelación cooperativa.
  Las sondas que ya están en curso pueden tardar en terminar. Se rechazan cambios
  de proyecto y ediciones concurrentes con una operación larga.
- Detalle, diagnóstico de puertos/servicios, WOL y acceso en terminal independiente.
  Los accesos usan el comando `open` y su almacén de credenciales; no muestran secretos.
- Crear proyectos vacíos, abrir VLF, seleccionar y guardar. Crear no copia las
  credenciales ni el inventario del proyecto anterior.
- Consulta de guardar/descartar/cancelar al cambiar o cerrar un proyecto con cambios.
- Configuración de red, descubrimiento, escaneo, carpeta/política de proyectos y
  nivel de registro. El formulario reutiliza la validación del comando `settings`.
- Eventos de sesión y acceso al historial del proyecto; paneles compatibles de plugins.
- `Ctrl+S`: aplica la edición del elemento y guarda el proyecto. `F5`: escanear.
- Presencia confirmada únicamente por escaneo de esta sesión, no por antigüedad
  de `lastSeen`. Abrir la ventana no inicia un escaneo.

## Distribución y límites

El build Windows incluye recursos GUI y requiere el extra `[gui]`. Se mantiene
el mismo `lanip.exe`, sin un séptimo launcher. Windows necesita WebView2 Runtime.
Linux necesita un motor compatible de pywebview (GTK/WebKit o Qt); el empaquetado
gráfico Linux no se ha validado en este cambio y los builds Linux publicados
siguen siendo CLI/TUI en 0.3.3.

La GUI no sustituye las pantallas especializadas de LANACCESS o LANWIRE. El
formulario de configuración ofrece una selección de opciones, no todas las
opciones avanzadas ni la administración completa de plugins.

## Pruebas

```powershell
.venv\Scripts\python.exe -m pytest tests/test_desktop_gui.py tests/test_modes.py
$env:PYTHONPATH = "src"
.venv\Scripts\python.exe tests/gui_native_smoke.py
# Opcional: instalar playwright en el entorno de desarrollo; requiere Edge.
$env:LANCTL_GUI_BROWSER_TESTS = "1"
.venv\Scripts\python.exe -m pytest tests/test_desktop_browser.py
```

La prueba nativa usa exclusivamente una carpeta temporal y no escanea la red.
El test de navegador utiliza respuestas simuladas y prueba formularios, filtros,
guardado, creación de proyectos y tamaños de ventana.

## Diseño Grafito y lima

La GUI utiliza la misma identidad del centro LANCTL. El inventario ocupa el
área principal completa. Una barra inferior reúne las acciones del equipo
seleccionado. El doble clic abre su ficha en pestañas: Resumen, Editar, Grupos,
Puertos y servicios y Registro completo. Se pueden editar nombre, alias,
descripción, icono, confirmación, IP e IDF mediante los servicios existentes.
Los grupos se añaden o retiran con sus propias acciones transaccionales.
La ficha muestra todos los campos guardados, ocultando secretos y referencias
de credenciales. Abrirla no inicia sondas: la inspección de puertos se solicita
expresamente. Los cambios pendientes se consultan al cerrar la ficha.

El escaneo comienza al pulsar su botón, sin una confirmación adicional del
navegador. HTTP/HTTPS, FTP, SMB, RDP, RTSP y Radmin se abren directamente en
sus aplicaciones; SSH, Telnet y TR-064 conservan su terminal interactiva.

Los controles separan escaneo, búsqueda, filtros y presentación. «Vista
esencial» muestra las columnas de uso habitual; «Completa» permite consultar
todos los campos con desplazamiento horizontal y «Columnas» personaliza la
selección. Se conservan la selección de columnas y las anchuras guardadas.
`Ctrl+K` enfoca la búsqueda; `Ctrl+S`, deshacer/rehacer, menú contextual,
plugins, historial y protección de cambios pendientes mantienen sus funciones.
El tema estándar se presenta en grafito y lima; los temas personalizados
conservan sus tokens y sus identificadores públicos de componentes.

«Nuevo grupo» crea un grupo con nombre y descripción (máximo 42 caracteres),
incluso sin seleccionar un equipo. También aparecen en el selector los grupos
vacíos del proyecto. «Más filtros» permite combinar fabricante, protocolo,
confirmación y equipos con/sin grupo, además de estado, grupo y búsqueda.
«Limpiar filtros» restablece la lista sin alterar el inventario.

Las pestañas superiores se sustituyen por el menú «Paneles» de la barra inferior,
que conserva el acceso a paneles de plugins e historial. El botón «CLI» inferior
abre `lanip --cli` en la terminal del sistema, independientemente de la consola
general de LANCTL.

La configuración incluye red y DHCP, método/perfil/orden/concurrencia y límites
del escaneo, identificación de servicios, reglas de retención de desconectados,
carpeta/política/intervalo de proyectos, nivel/limpieza/conservación de logs y
encadenamiento de órdenes CLI. Las opciones con valores cerrados se presentan
como selectores y se validan con el parser de configuración existente.

La descripción de los **elementos** admite texto multilínea sin el límite
anterior de 42 caracteres, tanto al importar como al editar mediante GUI/CLI.
Los grupos conservan su contrato propio de descripción.
En la ficha, la pertenencia a grupos se modifica con casillas; se puede crear
y añadir un grupo sin abrir otro diálogo. Las ediciones de identificación
pendientes se guardan antes de aplicar cambios de grupos.

La barra inferior incluye «LANCTL» para abrir el centro GUI. Las acciones de
equipo se deshabilitan según selección, protocolos disponibles, plugins y
posibilidad de ejecutar acciones reales. El cierre nativo solicita la decisión
de guardado sin bloquear el hilo de Windows; un escaneo en curso se cancela
antes de cerrar. En Windows compatible se aplica el tema oscuro a la barra
nativa conservando minimizar, maximizar y cerrar.
