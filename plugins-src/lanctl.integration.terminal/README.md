# Windows Terminal Integration

Plugin LCP **trusted**: ejecuta código Python con los permisos del usuario,
crea archivos propios y lanza procesos. Los permisos LCP no son un sandbox.
No se activa ni instala automáticamente.

Desde LANIP (CLI o consola del TUI):

```text
terminal-integration help
terminal-integration status
terminal-integration create cli
terminal-integration create tui
terminal-integration configure windows-terminal
terminal-integration configure inherited
terminal-integration open cli
terminal-integration open tui
terminal-integration remove cli
terminal-integration remove tui
```

Desde PowerShell anteponer `lanip` a esos comandos. `create` crea o actualiza
solo el fragmento del plugin: LANCTL abre `--cli`, LANIP abre `--tui`.
Un perfil personal con el mismo nombre provoca un aviso, nunca se sobrescribe.
`remove` conserva una copia `.json.removed`. Reiniciar Terminal tras crear perfiles.
Las preferencias son locales a este PC/usuario, fuera de proyectos y Git:
`%LOCALAPPDATA%/LANCTL/terminal-integration/preferences.json`.

Por defecto se hereda la terminal. La opción `windows-terminal` redirige el
arranque TUI de LANIP (también por el orquestador LANCTL) a una ventana nueva;
conserva argumentos y directorio actual. CLI y comandos normales no se redirigen.
Dentro de Windows Terminal, SSH o un proceso ya relanzado no vuelve a abrirse.
Si no se puede abrir Terminal, se registra el error y se mantiene la terminal
actual. `open` solicita expresamente una ventana nueva, sin depender de perfiles
personales existentes. El proceso hijo necesita cargar la misma instalación.

Requiere Windows, `wt.exe` y los launchers instalados. En otros sistemas `help`
funciona pero las acciones Windows se rechazan; el arranque nativo no cambia.
No cambia la terminal predeterminada de Windows, ni almacena contraseñas, ni
eleva permisos. No detecta configuraciones portables de Terminal en rutas
personalizadas. Este primer proveedor no incluye editor visual en SETTINGS,
paneles divididos ni redirección del TUI de LANWIRE/LANRACK.

El Core debe incluir `core/terminal_integration.py` para redirigir automáticamente;
los ejecutables antiguos solo podrán utilizar los comandos explícitos del plugin.
Funciones públicas estables: `TerminalIntegration.Profile.Command.Run` y
`TerminalIntegration.Runtime.Tui.Route`. Errores a través de `api.errors`, acciones
mediante `api.log`; ningún evento existente se renombra.
