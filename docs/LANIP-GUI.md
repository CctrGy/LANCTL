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
