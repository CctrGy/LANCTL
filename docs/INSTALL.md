# Instalación y actualización

GitHub Releases es el canal de distribución binaria de LANCTL. Los scripts de
instalación no compilan código: seleccionan un artefacto exacto para la versión,
SO y arquitectura, descargan `SHA256SUMS.txt` y fallan antes de instalar si la
verificación no coincide.

## Windows

Uso rápido (implica confiar en el script remoto):

```powershell
irm https://raw.githubusercontent.com/CctrGy/LANCTL/main/install.ps1 | iex
```

Método verificable recomendado:

```powershell
Invoke-WebRequest https://github.com/CctrGy/LANCTL/releases/download/vVERSION/install.ps1 -OutFile install.ps1
Invoke-WebRequest https://github.com/CctrGy/LANCTL/releases/download/vVERSION/SHA256SUMS.txt -OutFile SHA256SUMS.txt
Get-FileHash .\install.ps1 -Algorithm SHA256
# Comparar manualmente con la línea install.ps1 de SHA256SUMS.txt:
.\install.ps1 -Channel stable
```

Opciones principales: `-Channel stable|beta`, `-Version VERSION`,
`-Mode standard|monitor`, `-Portable`, `-ConfigureAccess`, `-Yes` y
`-Uninstall`. El ZIP portable no modifica PATH ni instala servicios. El setup
Inno instala en Program Files y puede añadir LANCTL al PATH. Sin un certificado
de firma configurado en GitHub Secrets, Windows mostrará editor desconocido o
SmartScreen; la verificación SHA-256 sigue siendo obligatoria.

El Setup interactivo ofrece crear la primera cuenta administrativa de acceso
remoto del servicio mediante `lanaccess remote-setup`. El asistente pide usuario,
contraseña y confirmación en su propia ventana, conserva cuentas existentes y
permite omitir el paso. No activa SSH/HTTPS ni abre puertos; consulta
[la configuración de acceso](ACCESS.md#cuenta-inicial-desde-el-instalador-de-windows).
La instalación silenciosa omite este asistente.

### Idioma del asistente, idioma de LANCTL y completado

El Setup ofrece **English** y **Español** antes de empezar. Las páginas,
componentes, tareas y mensajes propios del asistente usan el idioma elegido;
el desinstalador reutiliza el idioma de la instalación. No cambia por ello
el idioma de LANCTL: una página independiente permite elegirlo. En una
instalación nueva se propone el equivalente al idioma del asistente y, si no
está incluido, inglés.

Los idiomas del programa proceden de `bundled/languages/*.lang`, validados e
incluidos en esa versión. No se consulta ni descarga contenido durante Setup:
la lista funciona sin conexión y crece al distribuir más catálogos oficiales.
Solo se instala el idioma elegido y el respaldo inglés. Los textos todavía no
catalogados conservan su comportamiento actual; la cobertura completa de GUI
y TUI sigue en P100.

Las actualizaciones conservan el idioma y los catálogos personalizados. Para
cambiar el idioma del programa durante una actualización, selecciona el idioma
y marca **Cambiar el idioma actual del programa**. Esta operación no sustituye
una traducción personalizada que ya esté instalada y validada.

La casilla **Activar autocompletado de comandos en CMD con Clink** es
independiente del PATH. Está seleccionada inicialmente para conservar el
comportamiento de versiones anteriores; después se conserva la elección del
asistente. Solo registra la carpeta de esta distribución para el usuario
original, si Clink está disponible. Desmarcarla retira únicamente ese registro
del usuario actual, sin afectar carpetas ajenas. No instala Clink ni integra
PowerShell. La retirada desde otra cuenta sigue requiriendo certificación P48.

Ejemplo de instalación silenciosa:

```powershell
.\LANCTL-VERSION-windows-x64-setup.exe /VERYSILENT /LANG=es /PROGRAMLANG=es /TASKS="clink"
# Cambiar expresamente el idioma de una instalación existente:
.\LANCTL-VERSION-windows-x64-setup.exe /VERYSILENT /LANG=en /PROGRAMLANG=en /CHANGEPROGRAMLANG=1 /MERGETASKS="!clink"
```

`/LANG` elige el asistente y `/PROGRAMLANG` el programa. Sin
`/CHANGEPROGRAMLANG=1`, una actualización conserva la preferencia efectiva.
Los códigos no incluidos y los valores de cambio distintos de 0/1 se rechazan.
Setup comprueba el código de salida al preparar las preferencias, antes de
abrir la creación opcional de cuentas; no confirma la configuración si falla.

Estos cambios tienen pruebas de servicio y contratos del asistente. La
compilación y el recorrido visual/elevado del Setup en Windows son una
verificación adicional; el job `inno-source-check` de CI comprueba la sintaxis
del asistente con archivos inertes, que nunca se instalan ni publican.

## Linux y Raspberry Pi OS 64-bit

### Asistente gráfico Linux

En Debian, Ubuntu y derivados con APT, el artefacto
`LANCTL-VERSION-linux-ARQUITECTURA-setup.run` incluye el asistente Qt y el DEB.
No necesita Python instalado. Descárgalo para tu arquitectura (`amd64` o
`arm64`) y ábrelo desde tu sesión gráfica, **sin sudo**:

```bash
bash ./LANCTL-0.3.4-alpha.2-linux-amd64-setup.run
```

También puedes darle permiso de ejecución y abrirlo desde el gestor de archivos.
La ventana ofrece:

- Idioma del instalador: English/Español; idioma del programa desde los catálogos
  oficiales de esa distribución, propuesto según el idioma del asistente.
- Tema inicial con muestra visual, seis plugins opcionales y conservación de
  preferencias existentes. El cambio de idioma en una actualización requiere
  marcar su casilla expresamente.
- Activación opcional del servicio LANMON, herramientas de red, completado de
  comandos principales en Bash y accesos al menú/escritorio. El archivo Lua de
  Clink pertenece a Windows; Linux no lo instala.
- Creación opcional de la primera cuenta administrativa remota del servicio,
  con contraseña/confirmación, sin activar SSH/HTTPS. Las cuentas existentes
  permanecen intactas. Las contraseñas viajan por stdin al helper privilegiado;
  no se guardan en argumentos ni archivos del instalador.
- Apertura de LANCTL al terminar o preparación del primer escaneo en LANIP,
  que requiere confirmar la interfaz/rango antes de sondear.

El DEB instala todos los launchers en `/opt/lanctl` y sus comandos en `/usr/bin`;
son componentes obligatorios. Los plugins se seleccionan para una instalación
nueva y no se activan sus permisos automáticamente. Una casilla de servicio
sin marcar conserva el estado de un servicio existente.

APT instala las dependencias gráficas del DEB y las herramientas opcionales
seleccionadas. El bootstrap instala requisitos del asistente que falten
(bibliotecas XCB, Polkit, xdg-user-dirs) mediante la autenticación del escritorio;
si falta Polkit y no hay terminal, muestra el comando para instalarlo y reabrir
el asistente. No descarga Python ni modifica archivos de inicio del shell.
Las operaciones de paquetes y servicio solicitan autenticación con Polkit;
la ventana y la configuración personal siguen ejecutándose como usuario normal.
La instalación de dependencias ausentes requiere repositorios APT accesibles.

El resumen precede a cualquier instalación. La página de progreso muestra los
fallos y permite volver atrás/reintentar; no declara éxito ni desinstala paquetes
ya aplicados si falla una operación posterior. El asistente conserva sus archivos
extraídos hasta cerrarse. `--check` verifica el contenido sin instalar;
`--extract NUEVO_DIRECTORIO` permite inspeccionarlo.

Compilación: `scripts/build-linux.sh VERSION` genera también el `.run`.
Para empaquetar de nuevo ejecutables congelados ya comprobados de la misma
versión, usa `scripts/package-linux.sh VERSION`; el asistente comprueba las
versiones de los seis launchers antes de crear el paquete. La generación aislada
del asistente es `python scripts/build-linux-setup.py RUTA_AL_DEB`.
Las dependencias de compilación Qt/PyInstaller se instalan en el entorno de
construcción; el workflow de release las incluye para ambas arquitecturas.


Uso rápido:

```sh
curl --proto '=https' --tlsv1.2 -fsSLo install.sh https://raw.githubusercontent.com/CctrGy/LANCTL/main/install.sh
sudo bash install.sh --channel stable
```

Descarga `install.sh` y su checksum por separado para el procedimiento
verificable. Se admiten DEB nativos `amd64` y `arm64`; ARM64 se construye en un
runner ARM nativo. Cada artefacto solo se declara verificado después de probarlo
en la arquitectura real; una validación estática no equivale a esa prueba. El
tarball es una alternativa portable explícita mediante
`--tarball` y no instala systemd. El DEB usa `/opt/lanctl`, `/usr/bin/lanctl`,
`/etc/lanctl` y `/var/lib/lanctl`, y crea un usuario `lanctl` sin shell. El modo
Monitor instala la unidad, pero no la inicia hasta que exista un proyecto activo.
La CLI ejecutada por un usuario normal guarda configuración e inventario bajo
`XDG_DATA_HOME/lanctl` (o `~/.local/share/lanctl`) y secretos bajo
`XDG_CONFIG_HOME/lanctl/access`. La unidad systemd fija `LANCTL_DATA_DIR` a
`/var/lib/lanctl` y `LANCTL_SECRET_DIR` a `/etc/lanctl/access`, evitando mezclar
datos interactivos y datos del servicio.

El DEB recomienda `iputils-ping`, `arping`, `smbclient` y `xdg-utils`. Son
integraciones opcionales: la CLI/TUI puede arrancar sin ellas, pero las técnicas
o acciones asociadas no estarán disponibles. El paquete conserva
`/var/lib/lanctl` y `/etc/lanctl` incluso durante un purge; eliminarlos requiere
una acción explícita del administrador.

## Datos, actualización y rollback

Los accesos gráficos de Windows utilizan `lanctl-window.exe` para evitar una
consola adicional. El host solo admite los seis launchers GUI. Desde una
terminal, los ejecutables habituales conservan `--gui`, CLI/TUI, redirecciones
y códigos de salida; la terminal existente no se oculta ni se cierra. Los
fallos de arranque gráfico quedan en los registros y muestran un aviso.

Los binarios y los datos están separados. En Windows, `Program Files\LANCTL`
contiene los ejecutables onefile `LANCTL.exe`, `lanip.exe`,
`lanwire.exe`, `lanrack.exe`, `lanaccess.exe`, `lanmon.exe` y `lanctl-window.exe`
además de la documentación; inventario, configuración,
logs, monitorización, plugins y proyectos viven en `ProgramData\LANCTL`. Los
secretos de usuario (DPAPI, host keys y configuración de acceso) viven bajo el
perfil local del usuario, o bajo `LANCTL_SECRET_DIR`/`LANCTL_DATA_DIR` cuando un
servicio establece explícitamente su raíz protegida. Las instalaciones estándar conservan
proyectos, configuración, almacenes cifrados y métricas. Los instaladores no
eliminan `/var/lib/lanctl`, `/etc/lanctl`, ProgramData ni proyectos durante una
desinstalación normal. Windows Setup y DEB realizan el reemplazo mediante sus
mecanismos transaccionales; el instalador portable prepara una carpeta nueva y
conserva la anterior antes del cambio.

El ZIP portable contiene `LANCTL.exe`, `lanip.exe`, `lanwire.exe`,
`lanrack.exe`, `lanaccess.exe`, `lanmon.exe`, `lanctl-window.exe`,
`README-portable.txt` y el marcador firmado `LANCTL.portable`; sus datos se guardan en `data/lanctl` dentro del propio
directorio portable. Un override `LANCTL_DATA_DIR` debe ser absoluto. Al detectar
datos de versiones antiguas junto al EXE, LANCTL los copia al nuevo destino sin
borrar el original y detiene la migración si encuentra un conflicto diferente.
LANWIRE usa esa misma raíz para `physical/idf.db`; no reutiliza las bases lógica
o de monitorización de LANCTL.

## Acceso remoto opcional

SSH y HTTPS siempre quedan apagados, incluso con `--mode monitor`. La opción
`--configure-access` ejecuta al final `lanctl access setup-wizard` en un terminal
local. El asistente pide credenciales mediante entrada segura, valida bind,
CIDR y puertos, genera claves/certificado y vuelve a apagar ambos servicios si
falla. En modo estándar usa datos de usuario; en modo Monitor usa el almacén de
servicio y los listeners quedan supervisados por el backend permanente.
`--yes` nunca habilita acceso remoto.

## Publicación

`.github/workflows/release.yml` ejecuta tests y validaciones, genera setup y ZIP
Windows, DEB/tarballs Linux amd64/arm64, calcula hashes sobre los artefactos
finales y publica al subir una rama `stable/VERSION` o un tag de versión.
Desde 0.3.3 los instaladores remotos seleccionan el canal estable por defecto;
el canal beta sigue disponible explícitamente. `workflow_dispatch` construye y
sube artefactos de CI sin crear una Release. La firma detached es opcional y usa
exclusivamente GitHub Secrets.
