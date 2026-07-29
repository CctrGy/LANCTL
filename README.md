# LANCTL

**Administración, inventario y diagnóstico de infraestructuras LAN desde Windows.**

LANCTL centraliza el descubrimiento de red, la identificación de dispositivos,
el acceso mediante protocolos de administración y la auditoría de cambios en
una CLI reproducible. Incluye una interfaz interactiva, una TUI a pantalla
completa y proyectos portables `.vlf` con verificación de integridad.

> **Estado del proyecto — `0.3.0-alpha.10`**
>
> Versión alfa orientada a desarrollo y validación. La interfaz, el formato de
> configuración y los comandos pueden cambiar antes de la primera versión estable.

## Capacidades

| Área | Funcionalidad |
| --- | --- |
| Descubrimiento | ICMP, ARP, mDNS, SSDP y WS-Discovery, según el perfil seleccionado |
| Inventario | Identidad por MAC, IP histórica, alias, nombre, fabricante, CNF, grupos y descripción |
| Diagnóstico | Ping, ARP activo, escaneo TCP e identificación basada en evidencias |
| Administración | SSH, TR-064, Telnet, HTTP(S), FTP, RDP, RTSP y SMB |
| Switching | Planificación y ejecución controlada de operaciones sobre switches Cisco |
| Seguridad | Credenciales protegidas con DPAPI y confirmación de operaciones sensibles |
| Presentación | CLI, consola interactiva, TUI y exportación a tabla, JSON, CSV, HTML o XML |
| Proyectos | Contenedores `.vlf` verificables con inventario SQLite, configuración y auditoría |
| Extensiones | Complementos `.lcp` con permisos, eventos y ámbitos definidos |

## Estado y alcance

LANCTL administra el modelo lógico de la red y los protocolos asociados a sus
elementos. El mapa físico de cableado no forma parte del alcance actual.

El repositorio contiene además `RackFimeware2`, un firmware experimental para
el monitor y gestor de rack basado en STM32F411. El firmware se mantiene como
componente independiente de la aplicación principal.

## Requisitos

- Windows 10 u 11.
- Python 3.10 o superior para ejecutar desde el código fuente.
- Acceso autorizado a la red y a los dispositivos que se quieran administrar.
- Privilegios suficientes para las operaciones de red utilizadas.

## Instalación para desarrollo

```powershell
git clone https://github.com/CctrGy/LANCTL.git
cd LANCTL
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

La instalación registra dos puntos de entrada equivalentes:

```powershell
lanctl --version
als --version
```

También puede ejecutarse directamente desde el repositorio:

```powershell
python main.py --help
run.cmd --help
```

## Inicio rápido

### Descubrir e inspeccionar la red

```powershell
lanctl list --normal
lanctl list --fast --active
lanctl list --accurate --progress
lanctl search NAS
lanctl ping ESP --arp
lanctl scan CAM1 --identify
```

Los perfiles ajustan el equilibrio entre velocidad y profundidad:

- `--fast`: prioriza ARP y reduce el tiempo de espera.
- `--normal`: combina ICMP, ARP, mDNS y SSDP.
- `--accurate`: añade reintentos, resolución de nombres y WS-Discovery.

`scan --identify` utiliza banners y sondas inocuas. Los resultados incluyen
servicio, producto, confianza y evidencia; el número de puerto por sí solo no
se considera una identificación suficiente.

### Consultar y exportar el inventario

```powershell
lanctl list --where "active and group=IOT and vendor~Amazon"
lanctl list --format json
lanctl list --format csv --output inventario.csv
lanctl list --format html --output inventario.html
```

Las expresiones `--where` admiten términos unidos mediante `and`, los estados
`active` e `inactive`, y los operadores `=`, `!=` y `~`. Se pueden consultar
los campos `ip`, `mac`, `alias`, `name`, `cnf`, `group`, `vendor`, `protocol`
y `description`. Las expresiones se interpretan sin ejecutar código.

### Abrir conexiones y terminales

```powershell
lanctl open NAS https
lanctl connect VD1 rdp
lanctl ssh SW
lanctl terminal NAS
lanctl open NAS ssh --dry-run
```

`open`, también disponible como `connect`, prepara el cliente correspondiente
para SSH, Telnet, HTTP, HTTPS, FTP, RDP, RTSP o SMB. La opción `--dry-run`
permite revisar el destino antes de iniciar una aplicación externa.

### Interfaces interactivas

```powershell
lanctl --cli
lanctl -tui
```

La CLI persistente permite seleccionar un elemento y reutilizarlo en comandos
posteriores. La TUI ofrece inventario, detalle y acciones contextuales a
pantalla completa.

Todos los comandos admiten `-h`, `--help` y `/?`.

## Configuración persistente

La configuración se almacena bajo `./data/als/`, relativa al ejecutable. Entre
las opciones más relevantes se encuentran:

```powershell
lanctl settings --scan-profile accurate
lanctl settings --progress on
lanctl settings --service-identification on
lanctl settings --workers 64 --timeout 0.8 --max-hosts 4096
lanctl settings --projects-directory "%USERPROFILE%\Documents\LanCTL"
```

Para revisar la configuración efectiva:

```powershell
lanctl settings
```

## Gestión de elementos

Los elementos se identifican principalmente por su MAC. Las modificaciones de
alias o nombre confirman automáticamente el registro; los elementos reservados
`GATEWAY` y `BRODCAST` están protegidos frente a operaciones destructivas.

```powershell
lanctl element 3C:E4:41:01:08:5E description "Echo Dot cocina"
lanctl cnf 3C:E4:41:01:08:5E O
lanctl element 3C:E4:41:01:08:5E delete
lanctl element 3C:E4:41:01:08:5E delete --yes
```

Sin `--yes`, la eliminación solicita confirmación. Si un dispositivo eliminado
continúa presente en la LAN, un descubrimiento posterior puede incorporarlo de
nuevo como elemento no identificado.

## Proyectos VLF

Un proyecto `.vlf` empaqueta la información necesaria para conservar y
verificar el estado de una LAN:

```powershell
lanctl project create Casa.vlf --name "Red de casa"
lanctl project info Casa.vlf
lanctl project verify Casa.vlf
lanctl project list Casa.vlf
lanctl project update Casa.vlf
lanctl project use Casa.vlf
```

Los nombres relativos se resuelven en `%USERPROFILE%\Documents\LanCTL\`. Se
puede indicar una ruta absoluta o cambiar el directorio desde `settings`.

El contenedor utiliza una estructura ZIP fija e incluye:

- Metadatos e identificación del proyecto.
- Inventario SQLite y copia de restauración.
- Configuración LAN y topología lógica.
- Credenciales cifradas como contenido opaco.
- Auditoría diaria de modificaciones.
- Hashes de contenido y checksum general.

`project create`, `project update` y `project use` seleccionan el VLF activo.
Cada entrada de auditoría renueva los hashes para conservar la validez del
contenedor. El contrato técnico se encuentra en [docs/VLF.md](docs/VLF.md).

## Registros y auditoría

LANCTL separa la actividad operativa de los cambios realizados sobre el
inventario:

| Registro | Ubicación | Contenido |
| --- | --- | --- |
| Programa | `./data/als/log/dd-mm-yyyy.log` junto al ejecutable | Comandos, conexiones, escaneos y mensajes operativos |
| Auditoría | `./logs/dd-mm-yyyy.log` dentro del VLF activo | Altas, bajas y cambios de los elementos |

La auditoría muestra los valores anteriores y nuevos, pero oculta las
referencias de credenciales. La limpieza automática del log operativo está
desactivada inicialmente y puede configurarse así:

```powershell
lanctl settings -log-cleanup on -log-retention-days 90
lanctl settings -log-cleanup off
```

Solo se eliminan archivos con el formato reconocido `dd-mm-yyyy.log`; el
registro del día actual y cualquier archivo ajeno al patrón permanecen intactos.

## Seguridad operacional

- Utiliza LANCTL únicamente en redes y equipos para los que tengas autorización.
- Revisa las operaciones de configuración antes de confirmarlas.
- Las consultas automatizadas por SSH se limitan a comandos de lectura permitidos.
- Las credenciales no se almacenan en texto plano y están vinculadas al usuario
  de Windows mediante DPAPI.
- Los proyectos VLF verifican estructura, tamaño, rutas internas, SQLite y hashes.
- No publiques `data/als/`, credenciales, claves ni proyectos reales en el repositorio.

## Complementos LCP

Los complementos `.lcp` amplían LANCTL mediante plugins, temas, idiomas,
automatizaciones, análisis, seguridad e interfaces. El formato declara permisos
y eventos para que cada complemento exponga explícitamente su alcance.

Consulta [docs/LCP.md](docs/LCP.md) para conocer el contrato y las restricciones
de seguridad.

## Capa de comandos Cisco

Las operaciones sobre switches se clasifican por riesgo, ofrecen una vista
previa y exigen confirmación cuando corresponde. Los comandos admitidos y el
modelo de ejecución están documentados en
[docs/cisco-command-layer.md](docs/cisco-command-layer.md).

## Calidad y pruebas

La suite automatizada se ejecuta con `unittest`:

```powershell
python -m unittest discover -s tests -v
```

Antes de distribuir una compilación también conviene verificar la sintaxis:

```powershell
python -m compileall -q app tests
```

## Compilación para Windows

```powershell
python -m pip install pyinstaller
.\build.cmd
.\dist\LANCTL.exe --version
```

Los directorios `build/` y `dist/` son artefactos locales y no se versionan.

## Firmware del rack

El proyecto de PlatformIO se encuentra en [`RackFimeware2`](RackFimeware2).
Incluye soporte para STM32F411CE Black Pill, Ethernet ENC28J60, sensores
DS18B20, relés, NeoPixel, consola USB y SSH.

Antes de instalarlo en una red real, sustituye las credenciales SSH de
desarrollo definidas en `RackFimeware2/platformio.ini`.

```powershell
cd RackFimeware2
pio run -e blackpill_f411ce
pio run -e blackpill_f411ce --target upload
pio device monitor -p COM50 -b 115200
```

## Estructura del repositorio

```text
app/           Aplicación y servicios de LANCTL
tests/         Pruebas automatizadas
docs/          Contratos y documentación técnica
assets/        Iconos y recursos visuales
packaging/     Metadatos de distribución
RackFimeware2/ Firmware experimental del rack
```

## Licencia

Este repositorio todavía no incluye un archivo de licencia. Mientras no se
publique una licencia explícita, se mantienen todos los derechos sobre el código.
