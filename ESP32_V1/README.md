# RackMonitor — Hardware V1

Firmware para ESP32-S3 orientado a monitorización y control autónomo de racks.
La administración normal usa Ethernet ENC28J60 y SSH. Wi-Fi permanece apagado.

## GPIO

| Función | GPIO |
|---|---:|
| OneWire TOP (2 × DS18B20) | 4 |
| OneWire BOTTOM (2 × DS18B20) | 5 |
| ENC28J60 MISO / SO | 6 |
| ENC28J60 MOSI / SI | 7 |
| ENC28J60 SCLK | 15 |
| ENC28J60 CS | 16 |
| ENC28J60 INT | 17 |
| ENC28J60 RESET | 10 |
| Relé FAN1 | 11 |
| Relé FAN2 | 12 |
| 3 × NeoPixel | 13 |
| Botones | 1, 2, 40, 41, 42 |

Cada bus OneWire necesita una resistencia pull-up, normalmente de 4,7 kΩ, a
3,3 V. Los relés se consideran activos con nivel alto. Durante el reset los GPIO
pueden quedar flotantes: el hardware debe incluir resistencias que mantengan los
relés en el estado seguro deseado.

## Comportamiento térmico

- TOP y BOTTOM calculan la media de sus dos sondas.
- Con una sola sonda válida, el grupo funciona en modo degradado.
- Dos sondas del mismo grupo que difieran más del límite generan `MISMATCH`.
- La temperatura de control es la mayor de las medias TOP/BOTTOM disponibles.
- Sin ninguna lectura válida, o ante discrepancia, se activa el failsafe y ambos
  ventiladores se encienden.
- Valores iniciales: FAN1 a 28 °C, FAN2 a 32 °C e histéresis de 2 °C.

## Configuración transaccional

Los comandos de configuración solo modifican `candidate`. `config save` valida,
guarda en NVS y actualiza `running/startup`. `config discard` cancela los cambios.
Los cambios de red requieren reinicio después de guardarlos.

```text
show temperature
show fan
show network
show running-config

temperature fan1-on 28
temperature fan2-on 32
temperature hysteresis 2
temperature mismatch 3

network dhcp
network static 192.168.1.50 255.255.255.0 192.168.1.1
network dns 192.168.1.1 1.1.1.1
hostname rackmonitor-01

config pending
config diff
config discard
config save
reboot
```

## Compilación y USB

`platformio.ini` habilita USB CDC/JTAG nativo y fija el puerto configurado para
carga y monitor. Credenciales SSH se suministran mediante `build_flags`.

```powershell
pio run
pio run --target upload
pio device monitor
```

La primera ejecución genera una clave de host ED25519 en LittleFS. Cierra una
sesión con `exit`, `logout`, `quit` o Ctrl+D.

La misma CLI está disponible por USB con `pio device monitor`. SSH y USB
comparten el mismo procesador de comandos y la misma configuración candidate,
running y startup. En USB, `exit`, `logout` o `quit` cierran la sesión lógica;
pulsa Enter para abrirla de nuevo.

## Limitaciones V1

- El driver ENC28J60 usado con Arduino-ESP32 2.x asigna la MAC local
  `02:00:00:12:34:56`. Es válida para un único prototipo, pero deberá sustituirse
  por una MAC local única antes de conectar varios RackMonitor a la misma LAN.
- Los botones están inicializados con pull-up, pero sus funciones todavía no
  están asignadas.
- El stack, API, proxy SSH, OLED y Wi-Fi temporal quedan reservados para fases
  posteriores.

## Diagnóstico ENC28J60

Existe un entorno temporal que conserva intacto el firmware RackMonitor y carga
un analizador de registros SPI sin red, SSH, sensores ni relés:

```powershell
pio run -e enc28j60-diagnostic --target upload
pio device monitor
```

Para volver al firmware normal:

```powershell
pio run -e esp32-s3-devkitc-1 --target upload
```

El firmware normal es el entorno predeterminado. Por tanto, desde
`ESP32_V1` también puede compilarse y cargarse con:

```powershell
pio run --target upload
```
