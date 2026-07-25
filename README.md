# LANCTL

LANCTL es una herramienta de línea de comandos para descubrir, inventariar y
administrar dispositivos de una red local. El repositorio también incluye el
firmware experimental `ESP32_V1` para monitorización y control de racks.

> Estado: `0.3.0-alpha.1` — prototipo en desarrollo.

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
- Firmware ESP32-S3 para sensores de temperatura, ventiladores, Ethernet y SSH.

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
lanctl virtual search NAS
lanctl virtual scan NAS
lanctl virtual terminal NAS
```

También se puede ejecutar directamente desde el código fuente:

```powershell
python main.py virtual list
run.cmd virtual list
```

Todos los comandos aceptan `-h`, `--help` o `/?`.

## Configuración y datos locales

LANCTL crea sus archivos de trabajo en `data/als/`. Este directorio puede
contener inventario, registros y credenciales vinculadas al usuario de Windows,
por lo que está excluido del repositorio.

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

## Firmware ESP32

El proyecto de PlatformIO está en [`ESP32_V1`](ESP32_V1). Incluye soporte para
ESP32-S3, Ethernet ENC28J60, sensores DS18B20, relés, NeoPixel, consola USB y
SSH. Consulta su README para el mapa GPIO y los comandos disponibles.

Antes de instalar el firmware en una red real, cambia las credenciales SSH de
desarrollo definidas en `ESP32_V1/platformio.ini`.

```powershell
cd ESP32_V1
pio run -e esp32-s3-devkitc-1
pio run -e esp32-s3-devkitc-1 --target upload
pio device monitor
```

## Estructura

```text
app/          Aplicación Python
tests/        Pruebas automatizadas
docs/         Documentación técnica
assets/       Iconos y recursos
packaging/    Metadatos del ejecutable
ESP32_V1/     Firmware PlatformIO
```

## Licencia

Este repositorio no incluye todavía un archivo de licencia. Hasta que se añada
uno, se mantienen todos los derechos sobre el código.
