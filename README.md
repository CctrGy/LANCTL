# LANCTL

LANCTL es una herramienta de línea de comandos para descubrir, inventariar y
administrar dispositivos de una red local. El repositorio también incluye el
firmware experimental `RackFimeware2` para monitorización y control de racks.

> Estado: `0.3.0-alpha.6` — prototipo en desarrollo.

## Funciones principales

- Descubrimiento LAN mediante ICMP, ARP o modo híbrido.
- Inventario persistente identificado por dirección MAC.
- Alias, nombres, grupos y descripciones de dispositivos.
- Salida en tabla, JSON y CSV.
- Terminales SSH y TR-064.
- Almacén local de credenciales protegido con DPAPI en Windows.
- Capa de comandos para switches Cisco con vista previa y confirmación de
  operaciones sensibles.
- Escaneo de puertos TCP.
- Firmware STM32F411 para sensores de temperatura, ventiladores, Ethernet y SSH.

## Requisitos

- Windows
- Python 3.10 o superior
- Acceso a la red local que se desea administrar

## Instalación

```powershell
git clone https://github.com/CctrGy/LANCTL.git
cd LANCTL
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Después de instalarlo se pueden usar los comandos `lanctl` o `als`.

## Uso rápido

```powershell
lanctl --help
lanctl virtual --help
lanctl virtual list
lanctl virtual list --discovery hybrid --show-discovery
lanctl virtual list --show-detection
lanctl list --fast --active
lanctl list --normal
lanctl list --accurate --progress
lanctl list --where "active and group=IOT and vendor~Amazon"
lanctl list --format html --output inventario.html
lanctl virtual search NAS
lanctl scan CAM1 --identify
lanctl open NAS https
lanctl connect VD1 rdp
lanctl virtual element 3C:E4:41:01:08:5E delete
lanctl ping ESP
lanctl ping ESP --arp
lanctl ping ESP --method ping
lanctl virtual scan NAS
lanctl virtual terminal NAS
lanctl --gui
lanctl -tui
```

`ping` realiza una comprobación puntual sin modificar el inventario. El modo
`auto` combina ICMP y ARP activo, por lo que puede detectar equipos de la LAN
que bloquean respuestas de ping. Dentro de `lanctl --gui`, `select ELEMENTO`
permite omitir el selector en las siguientes comprobaciones.

También se puede ejecutar directamente desde el código fuente:

```powershell
python main.py virtual list
run.cmd virtual list
```

Todos los comandos aceptan `-h`, `--help` o `/?`.

## Perfiles, identificación y consultas

`list` dispone de tres perfiles. `--fast` prioriza ARP y velocidad;
`--normal` combina ICMP, ARP, mDNS y SSDP; `--accurate` añade reintentos,
resolución de nombres y WS-Discovery. El progreso solo se dibuja en una
terminal interactiva, por lo que JSON, archivos y scripts permanecen limpios.

`scan --identify` no presupone que un puerto determine el protocolo: utiliza
banners y sondas inocuas para aportar servicio, producto, confianza y
evidencia. La clasificación del tipo de equipo es una deducción explícita, no
una afirmación sin respaldo.

Las consultas `--where` admiten términos unidos con `and`, los estados
`active`/`inactive` y los operadores `=`, `!=` y `~`. Los campos disponibles
son `ip`, `mac`, `alias`, `name`, `cnf`, `group`, `vendor`, `protocol` y
`description`. No se evalúa código dentro de la expresión.

Las tablas se pueden almacenar como `table`, `json`, `csv`, `html` o `xml`.
El comando común `open` (alias `connect`) prepara clientes SSH, Telnet, HTTP,
HTTPS, FTP, RDP, RTSP y SMB; `--dry-run` permite revisar el destino sin abrirlo.

Opciones persistentes relevantes:

```powershell
lanctl settings --scan-profile accurate
lanctl settings --progress on
lanctl settings --service-identification on
lanctl settings --workers 64 --timeout 0.8 --max-hosts 4096
```

Para eliminar por completo una MAC huérfana del inventario y de todos sus
grupos:

```powershell
lanctl element 3C:E4:41:01:08:5E delete
lanctl element 3C:E4:41:01:08:5E delete --yes
```

Sin `--yes` se solicita confirmación. `GATEWAY` y `BRODCAST` están protegidos.
Si el equipo continúa presente en la LAN, el próximo `list` volverá a
descubrirlo como un elemento nuevo con `CNF=X`.

## Configuración y datos locales

LANCTL crea sus archivos de trabajo en `data/als/`. Este directorio puede
contener inventario, registros y credenciales vinculadas al usuario de Windows,
por lo que está excluido del repositorio.

La limpieza interna de registros está desactivada inicialmente. Puede activarse
y configurarse con:

```powershell
run settings -log-cleanup on
run settings -log-retention-days 90
run settings -log-cleanup off
```

Al arrancar, LANCTL elimina únicamente archivos `dd-mm-yyyy.log` más antiguos
que el periodo configurado. Nunca elimina el registro del día actual ni otros
archivos que encuentre en el directorio de logs.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

## Crear el ejecutable de Windows

Instala PyInstaller y ejecuta:

```powershell
python -m pip install pyinstaller
.\build.cmd
.\dist\LANCTL.exe --version
```

Los directorios `build/` y `dist/` son artefactos locales y no se versionan.

## Firmware STM32

El proyecto de PlatformIO está en [`RackFimeware2`](RackFimeware2). Incluye
soporte para STM32F411CE Black Pill, Ethernet ENC28J60, sensores DS18B20,
relés, NeoPixel, consola USB y SSH. Consulta su README para el mapa GPIO y los
comandos disponibles.

Antes de instalar el firmware en una red real, cambia las credenciales SSH de
desarrollo definidas en `RackFimeware2/platformio.ini`.

```powershell
cd RackFimeware2
pio run -e blackpill_f411ce
pio run -e blackpill_f411ce --target upload
pio device monitor -p COM50 -b 115200
```

## Estructura

```text
app/          Aplicación Python
tests/        Pruebas automatizadas
docs/         Documentación técnica
assets/       Iconos y recursos
packaging/    Metadatos del ejecutable
RackFimeware2/ Firmware PlatformIO para STM32F411
```

## Licencia

Este repositorio no incluye todavía un archivo de licencia. Hasta que se añada
uno, se mantienen todos los derechos sobre el código.
