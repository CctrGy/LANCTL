# LANCTL

Suite CLI/TUI para descubrir, inventariar, diagnosticar y administrar
infraestructuras LAN desde Windows, Linux y Raspberry Pi OS.

> Versión actual: **0.3.1-beta.1**. Es una beta: conserva copias de seguridad
> de los proyectos y no la utilices como única fuente de inventario.

Los binarios publicados son autocontenidos y no requieren Python.

## Aplicaciones

| Ejecutable | Ámbito |
| --- | --- |
| `lanctl` | Orquestador raíz de la suite |
| `lanip` | Descubrimiento, inventario IP/MAC, diagnóstico y TUI principal |
| `lanwire` | Cableado, puertos, paneles y topología física |
| `lanrack` | Salas técnicas, racks, unidades U y equipos |
| `lanaccess` | Usuarios, credenciales y acceso remoto |
| `lanmon` | Monitorización, eventos, incidencias e historial |

Cada aplicación puede iniciarse directamente o mediante el orquestador:

```text
lanip list --active
lanctl lanip list --active
lanwire list
lanctl lanwire list
lanrack --tui
lanaccess --tui
lanmon status
```

Los comandos de un dominio no se mezclan con los demás. `list`, `scan`,
`element` y `project` pertenecen a `lanip`, no al ejecutable raíz.

## Estado actual

El desarrollo activo se centra en CLI y TUI. La antigua GUI está congelada, no
se empaqueta y no forma parte de los binarios publicados. Solo puede ejecutarse
desde código con el extra `gui` y `LANCTL_ENABLE_LEGACY_GUI=1`; consulta
[LEGACY-GUI.md](docs/LEGACY-GUI.md).

LANCTL incluye:

- Descubrimiento ICMP, ARP y WS-Discovery, ampliable mediante plugins.
- Inventario por MAC, IP, CNF, alias, nombre, fabricante y grupos.
- Identificación de servicios mediante banners y evidencias.
- SSH, HTTPS, HTTP, Telnet, FTP, RDP, RTSP y SMB.
- Proyectos `.vlf` con inventario, configuración, auditoría y hashes.
- Historial, monitorización, incidencias y Wake-on-LAN.
- Plugins `.lcp` con permisos y runtimes declarativo, aislado o trusted.
- Exportación a tabla, JSON, CSV, HTML, XML y YAML.

## Instalación

### Windows

```powershell
Invoke-WebRequest https://github.com/CctrGy/LANCTL/releases/download/vVERSION/install.ps1 -OutFile install.ps1
Invoke-WebRequest https://github.com/CctrGy/LANCTL/releases/download/vVERSION/SHA256SUMS.txt -OutFile SHA256SUMS.txt
Get-FileHash .\install.ps1 -Algorithm SHA256
# Compara el hash con SHA256SUMS.txt antes de ejecutar:
.\install.ps1 -Channel beta
```

La distribución ofrece un Setup x64 y un ZIP portable. La instalación estándar
coloca los seis ejecutables en `C:\Program Files\LANCTL` y puede añadirlos al
`PATH`. Los datos nunca se escriben dentro de Program Files.

### Linux y Raspberry Pi OS

```sh
curl --proto '=https' --tlsv1.2 -fsSLo install.sh \
  https://raw.githubusercontent.com/CctrGy/LANCTL/main/install.sh
sudo bash install.sh --channel beta
```

Se generan DEB y tarballs portables nativos para `amd64` y `arm64`.
Raspberry Pi OS debe ser de 64 bits para el artefacto ARM64. El DEB instala en
`/opt/lanctl`, enlaza los comandos en `/usr/bin` e incluye la unidad systemd.
El tarball no instala servicios.

Consulta [INSTALL.md](docs/INSTALL.md) para instalación offline, selección de
versión, modo Monitor, actualización, rollback y desinstalación.

## Inicio rápido

### Interfaces

```text
lanip --tui
lanip --tui PLUGINS
lanip --tui PROJECTS
lanip --tui SETTINGS
lanip --cli
```

`lanctl --tui` y `lanctl --cli` son los puntos de entrada generales. Dentro
del repositorio también pueden usarse `run.cmd --tui` y `run.cmd --cli`.

El TUI adapta tablas, overlays y pestañas al ancho disponible. El escaneo se
ejecuta en segundo plano, mantiene activo el teclado y puede cancelarse con
`Esc`. Los atajos visibles predeterminados son:

| Tecla | Acción |
| --- | --- |
| `F1` | Ayuda |
| `F2` | Información |
| `F3` | Ping |
| `F5` | Actualizar |
| `F7` | Plugins |
| `F9` | Proyectos |
| `F12` | Settings |
| `↑` / `↓` | Seleccionar |

También están disponibles `Ctrl+F` buscar, `Ctrl+S` guardar el proyecto,
`Ctrl+X` copiar la fila, `Ctrl+J` copiar JSON y `Ctrl+Q` cierre seguro.
Las asignaciones y su visibilidad se editan en `SETTINGS / TECLADO`.

### Descubrir e inspeccionar

```text
lanip list --fast --active
lanip list --normal
lanip list --accurate --progress
lanip scan NAS --identify --banners
lanip ping NAS --arp
lanip search NAS
```

El escaneo normal actualiza el inventario activo. Para descubrir equipos sin
abrir ni modificar un proyecto:

```text
lanip ephemeral --normal
lanip -e --fast --range 192.168.1.0/24
lanip ephemeral --ports 22,80,443 --json
```

### Consultar y exportar

```text
lanip list --where "active and group=IOT and vendor~Amazon"
lanip list --format json
lanip list --format csv --output inventario.csv
lanip call NAS --json
```

`--where` admite `and`, estados `active`/`inactive` y operadores `=`,
`!=` y `~`; las expresiones no ejecutan código.

### Editar elementos

Todas las modificaciones parten del comando raíz `element`:

```text
lanip element NAS -name HomeNAS
lanip element NAS -alias NAS -description "Almacenamiento principal"
lanip element NAS -cnf O -group ASSETS -protocol ssh
lanip element NAS delete
lanip element NAS delete --yes
```

Una cadena de opciones se valida y aplica como una transacción. Dispositivos y
grupos usan bloqueo conjunto, rollback y journal durable; cualquier journal
pendiente se recupera al abrir las bases. `GATEWAY` y `BRODCAST` están
protegidos frente a eliminación. Los estados CNF son `O`, `X`, `S`, `F`
y `-`.

### Proyectos VLF

Un proyecto nuevo se crea vacío por defecto:

```text
lanip project create Casa.vlf --name "Red de casa"
lanip project use Casa.vlf
lanip list --accurate
lanip project save
lanip project verify Casa.vlf
```

Para copiar explícitamente el inventario y los grupos activos:

```text
lanip project create Copia.vlf --clone-current
```

LANCTL impide cambiar o recargar un proyecto con cambios pendientes sin una
decisión explícita. Cada actualización crea copias de recuperación y verifica
el inventario guardado. `project update` solo actualiza el proyecto activo.
Consulta [VLF.md](docs/VLF.md) y [STORAGE.md](docs/STORAGE.md).

### SSH y credenciales de dispositivos

```text
lanip protocol NAS configure ssh --port 22
lanip credential NAS set ssh --username USUARIO
lanip ssh NAS probe
lanip ssh NAS fingerprint
lanip ssh NAS trust SHA256:HUELLA
lanip ssh NAS open
```

La contraseña se solicita mediante entrada segura. Para listar referencias sin
mostrar secretos:

```text
lanaccess list
lanip credential NAS list
```

### Acceso remoto a LANCTL

SSH y HTTPS permanecen desactivados hasta configurarlos localmente:

```text
lanip access init
lanip access configure ssh --bind 192.168.1.31 --cidr 192.168.1.0/24
lanip access user add administrador --role administrator
lanip access status
```

No existen credenciales predeterminadas. Las sesiones remotas están limitadas
al entorno LANCTL y aplican roles y permisos. Un servicio Windows en Session 0
no puede mostrar ventanas; `forced-view` devuelve ese estado y requiere un
agente interactivo. Consulta [ACCESS.md](docs/ACCESS.md).

### Plugins LCP

```text
lanip plugin verify complemento.lcp
lanip plugin install complemento.lcp
lanip plugin enable ID --grant-all
lanip plugin list
```

Los plugins quedan desactivados después de instalarse. Los trusted requieren
firma de un editor autorizado y confianza explícita. El runtime aislado impone
límites, pero no sustituye un sandbox del sistema operativo frente a código
hostil. Instala únicamente paquetes firmados y de confianza. Consulta
[LCP.md](docs/LCP.md).

## Datos y persistencia

| Entorno | Datos | Secretos |
| --- | --- | --- |
| Windows instalado | `C:\ProgramData\LANCTL` | Perfil local o raíz protegida del servicio |
| Linux interactivo | `$XDG_DATA_HOME/lanctl` | `$XDG_CONFIG_HOME/lanctl/access` |
| Servicio systemd | `/var/lib/lanctl` | `/etc/lanctl/access` |
| Portable | `data/lanctl` junto a los ejecutables | Raíz portable |

Los proyectos se guardan por defecto en la carpeta Documentos conocida por el
sistema, dentro de `LanCTL`. Los instaladores conservan proyectos,
configuración, métricas y secretos al desinstalar. Consulta
[CONFIGURATION.md](docs/CONFIGURATION.md).

## Desarrollo y validación

Requiere Python 3.10 o posterior:

```powershell
git clone https://github.com/CctrGy/LANCTL.git
cd LANCTL
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

```text
python lanctl.py /?
python lanip.py /?
python lanwire.py /?
python lanrack.py /?
python lanaccess.py /?
python lanmon.py /?
```

Validación:

```text
python -m pytest -q
python -m pytest -q -m legacy_gui
python -m ruff format --check .
python -m ruff check .
python -m bandit -q -r src -ll
python -m pip_audit . --strict
python tools/generate_error_catalog.py --check
python tools/generate_cli_reference.py --check
python -m compileall -q src tests
```

La última revisión local completó 616 pruebas principales, 18 de la GUI
congelada y 594 subpruebas. El catálogo contiene 874 puntos de error. CI no
ignora vulnerabilidades conocidas.

## Compilación

```powershell
.\scripts\build-windows.ps1 -Version 0.3.1-beta.1
```

```sh
./scripts/build-linux.sh 0.3.1-beta.1
```

Los builds generan metadatos, `SHA256SUMS.txt` y verifican el conjunto final.

## Estructura

```text
src/lanctl/
├── apps/
│   ├── ip/             LANIP
│   ├── wire/           LANWIRE
│   ├── rack/           LANRACK
│   ├── access/         LANACCESS y acceso remoto
│   └── monitor/        LANMON
├── bootstrap/          Entradas de los ejecutables
├── core/               Configuración, proyectos, persistencia y plugins
├── infrastructure/     Adaptadores de plataforma y distribución
└── shared/             Recursos compartidos

tests/                  Pruebas automatizadas
docs/                   Manuales y contratos
packaging/              Windows, Debian, systemd y portable
plugins-src/            Fuentes de plugins separados
bundled/                Complementos incluidos
```

## Documentación

- [Referencia completa del CLI](docs/CLI-REFERENCE.md)
- [Manual del TUI](docs/TUI.md)
- [Instalación](docs/INSTALL.md)
- [Persistencia y recuperación](docs/STORAGE.md)
- [Acceso remoto](docs/ACCESS.md)
- [Seguridad](docs/SECURITY.md)
- [Plugins](docs/LCP.md)
- [Limitaciones conocidas](docs/KNOWN-ISSUES.md)
- [Guía para beta testers](docs/BETA-TESTING.md)

Todos los comandos admiten `-h`, `--help` y `/?`.

## Licencia

El repositorio todavía no incluye una licencia explícita. Hasta que se añada,
se mantienen todos los derechos sobre el código.
