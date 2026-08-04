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
.\install.ps1 -Channel beta
```

Opciones principales: `-Channel stable|beta`, `-Version VERSION`,
`-Mode standard|monitor`, `-Portable`, `-ConfigureAccess`, `-Yes` y
`-Uninstall`. El ZIP portable no modifica PATH ni instala servicios. El setup
Inno instala en Program Files y puede añadir LANCTL al PATH. Sin un certificado
de firma configurado en GitHub Secrets, Windows mostrará editor desconocido o
SmartScreen; la verificación SHA-256 sigue siendo obligatoria.

## Linux y Raspberry Pi OS 64-bit

Uso rápido:

```sh
curl --proto '=https' --tlsv1.2 -fsSLo install.sh https://raw.githubusercontent.com/CctrGy/LANCTL/main/install.sh
sudo bash install.sh --channel stable
```

Descarga `install.sh` y su checksum por separado para el procedimiento
verificable. Se admiten DEB nativos `amd64` y `arm64`; ARM64 se construye en un
runner ARM nativo. El tarball es una alternativa portable explícita mediante
`--tarball` y no instala systemd. El DEB usa `/opt/lanctl`, `/usr/bin/lanctl`,
`/etc/lanctl` y `/var/lib/lanctl`, y crea un usuario `lanctl` sin shell. El modo
Monitor instala la unidad, pero no la inicia hasta que exista un proyecto activo.

## Datos, actualización y rollback

Los binarios y los datos están separados. En Windows, `Program Files\LANCTL`
contiene únicamente el EXE onefile y documentación; inventario, configuración,
logs, monitorización, plugins y proyectos viven en `ProgramData\LANCTL`. Los
secretos de usuario (DPAPI, host keys y configuración de acceso) viven bajo el
perfil local del usuario, o bajo `LANCTL_SECRET_DIR`/`LANCTL_DATA_DIR` cuando un
servicio establece explícitamente su raíz protegida. Las instalaciones estándar conservan
proyectos, configuración, almacenes cifrados y métricas. Los instaladores no
eliminan `/var/lib/lanctl`, `/etc/lanctl`, ProgramData ni proyectos durante una
desinstalación normal. Windows Setup y DEB realizan el reemplazo mediante sus
mecanismos transaccionales; el instalador portable prepara una carpeta nueva y
conserva la anterior antes del cambio.

El ZIP portable contiene solo `LANCTL.exe`, `README-portable.txt` y el marcador
firmado `LANCTL.portable`; sus datos se guardan en `data/lanctl` dentro del propio
directorio portable. Un override `LANCTL_DATA_DIR` debe ser absoluto. Al detectar
datos de versiones antiguas junto al EXE, LANCTL los copia al nuevo destino sin
borrar el original y detiene la migración si encuentra un conflicto diferente.

## Acceso remoto opcional

SSH y HTTPS siempre quedan apagados, incluso con `--mode monitor`. La opción
`--configure-access` ejecuta al final `lanctl access setup-wizard` en un terminal
local. El asistente pide credenciales mediante entrada segura, valida bind,
CIDR y puertos, genera claves/certificado y vuelve a apagar ambos servicios si
falla. `--yes` nunca habilita acceso remoto.

## Publicación

`.github/workflows/release.yml` ejecuta tests y validaciones, genera setup y ZIP
Windows, DEB/tarballs Linux amd64/arm64, calcula hashes sobre los artefactos
finales y publica únicamente en builds de tag. `workflow_dispatch` construye y
sube artefactos de CI sin crear una Release. La firma detached es opcional y usa
exclusivamente GitHub Secrets.
