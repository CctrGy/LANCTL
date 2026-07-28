# RackMonitor Firmware 2 — STM32F411CE

Migración del firmware `ESP32_V1` a una Black Pill STM32F411CE.

## Pines

| Función | STM32 |
|---|---|
| ENC28J60 MISO/SO | PB4 |
| ENC28J60 MOSI/SI | PB5 |
| ENC28J60 SCLK | PB3 |
| ENC28J60 RESET | PB6 |
| ENC28J60 CS | PB7 |
| ENC28J60 INT | PB8 |
| NeoPixel (3 LED) | PB10 |
| DS18B20 TOP (1 sonda) | PB1 |
| DS18B20 BOTTOM (1 sonda) | PB2 |
| Relé FAN1 | PA6 |
| Relé FAN2 | PA7 |

Los relés son activos en nivel alto. Durante el arranque se activan ambos como
estado seguro hasta disponer de lecturas válidas de temperatura.

## Cambios de arquitectura

- `ESP32-ENC28J60` se sustituye por `EthernetENC`.
- `Preferences/NVS` se sustituye por EEPROM emulada.
- `ESP.restart()` se sustituye por `NVIC_SystemReset()`.
- USB CDC ofrece la misma CLI por `COM50` mientras la aplicación está ejecutándose.
- `LibSSH-ESP32` se sustituye por wolfSSH/wolfCrypt, con SSHv2 real en el
  puerto 22, clave de host ECDSA P-256 estable y autenticación por contraseña.

## Acceso SSH

```powershell
ssh admin@IP_DEL_RACKMONITOR
```

La contraseña se define en `platformio.ini` mediante `SSH_PASSWORD`. El valor
incluido en el repositorio es solo un marcador y debe sustituirse antes de
compilar y cargar el firmware.

La clave privada de host se guarda localmente en `include/SshHostKey.h` y está
excluida de Git. Cada dispositivo o instalación debe generar su propia clave y
declarar `SSH_HOST_KEY_DER` y `SSH_HOST_KEY_DER_SIZE`; nunca reutilices ni
publiques una clave privada de producción. Usa `include/SshHostKey.example.h`
como contrato de integración.

## Compilar y cargar

```powershell
pio run
pio run -t upload
pio device monitor -p COM50 -b 115200
```

La carga usa el programador ST-Link configurado en `platformio.ini`. `COM50`
es el puerto CDC de la aplicación y se utiliza para la CLI serie y el diagnóstico.
