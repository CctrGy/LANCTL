# Comandos del repositorio

## Firmar Terminal Integration

```powershell
.\.venv\Scripts\python.exe repositoryTerminal\sign-terminal-plugin.py
```

Reutiliza (o crea) la clave Ed25519 en
`%LOCALAPPDATA%\LANCTL\publisher-keys\terminal-integration.pem`, fuera del
repositorio. Restringe el directorio al usuario actual y SYSTEM mediante ACL.
La clave no tiene contraseña: protege ese directorio y guarda una copia segura;
nunca la publiques. El paquete firmado queda en `dist/plugins/`.
Confiar en ese editor permite autorizar otros paquetes firmados con esa clave;
no es una firma comercial ni una autorización de terceros.

## Perfil de Windows Terminal

```powershell
.\repositoryTerminal\terminal-profile.cmd
.\repositoryTerminal\terminal-profile.cmd -DryRun
.\repositoryTerminal\terminal-profile.cmd -Executable "C:\Program Files\LANCTL\LANCTL.exe"
```

Crea para el usuario actual un perfil **LANCTL** que ejecuta `lanctl --cli`,
con el icono del ejecutable. Usa un fragmento en
`%LOCALAPPDATA%\Microsoft\Windows Terminal\Fragments\LANCTL\lanctl-cli.json`.
No modifica `settings.json`, no cambia el perfil predeterminado y no solicita
administrador. Si detecta un perfil llamado LANCTL en las configuraciones
estándar (Store, Preview o sin empaquetar) o fragmentos locales, no lo duplica
ni lo modifica. La detección conservadora también respeta perfiles comentados.
Instalaciones portables de Terminal con configuración en otras rutas no se
detectan. Cierra y abre Terminal para cargar el perfil. No guarda credenciales.
Para retirar el perfil generado basta con eliminar ese fragmento concreto.

Implementado mediante [fragmentos oficiales de Windows Terminal](https://learn.microsoft.com/en-us/windows/terminal/json-fragment-extensions).

## Compilación e instalación

Herramientas de mantenimiento para desarrolladores; no son comandos del Core
ni launchers instalados. No cargan configuraciones, plugins ni proyectos.

Desde la raíz del repositorio en CMD:

```bat
install
install build
install remote
install remote -Channel stable
install help
install -DryRun
```

En PowerShell se debe escribir `./install.cmd` en lugar de `install`, ya que
PowerShell no busca ejecutables en el directorio actual automáticamente.
El comando puede invocarse por ruta absoluta desde otra carpeta.

- **install**: detecta la versión del código, compila los seis launchers y el
  instalador con `scripts/build-windows.ps1 -AllowDirty`, y abre el Setup con UAC.
  No instala si falla el build. Incluye cambios sin commit; no hace Git/push.
- **build**: la misma compilación, sin ejecutar el instalador.
- **remote**: delega en `install.ps1` para descargar una release publicada,
  verificar sus hashes e instalarla. No usa los cambios locales.
- **-DryRun**: muestra el plan sin compilar, descargar ni instalar.

Se necesita Git, Python (preferentemente `.venv`) con PyInstaller y las
dependencias del proyecto, e Inno Setup 6. Estos comandos no instalan esas
dependencias automáticamente. Guarda el trabajo, conserva una copia de los
proyectos y cierra LANCTL antes de actualizar. No se desinstala previamente ni
se borra ProgramData para actualizar; el destino se elige en el asistente.

Los puntos de entrada remotos autónomos `install.ps1` e `install.sh` permanecen
en la raíz para conservar sus URLs y poder descargarlos sin el repositorio.
Los scripts de empaquetado permanecen en `scripts/`, usados también por CI.
Esta carpeta agrupa su acceso sin duplicar su implementación.

En Linux sigue disponible `bash install.sh` (release remota) y
`bash scripts/build-linux.sh VERSION` (compilación local). `install.cmd` y el
orquestador PowerShell de esta carpeta son específicos de Windows; no se
sustituye el comando estándar Unix `install`.

Estos scripts y esta documentación **sí se versionan**. Los resultados de
compilación en `build/` y `dist/`, datos, credenciales y proyectos siguen fuera
de Git según `.gitignore`.
