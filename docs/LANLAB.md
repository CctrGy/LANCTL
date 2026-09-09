# LANLAB Network Emulator

LANLAB permite probar inventario, filtros, historial y presentación de LANIP sin depender de una
LAN física. Su proveedor implementa el contrato común `DiscoveryProvider` y devuelve
`DiscoveryResult` con `source=simulated`, proveedor, escenario y semilla.

## Inicio rápido

```bat
lanip lab generate --name oficina --profile office --devices 80 --seed 84521
lanip lab validate oficina
lanip lab start oficina
lanip list
lanip lab evolve --seconds 120
lanip lab stop
```

La misma semilla, CIDR, perfil y cantidad producen los mismos dispositivos. Los perfiles disponibles
son `home`, `office`, `datacenter`, `industrial` y `chaotic`; los tipos son `snapshot`, `timeline` y
`chaos`.

## Red manual

```bat
lanip lab network create --name pequeña --cidr 192.0.2.0/24
lanip lab device add pequeña --ip 192.0.2.10 --mac 02:00:00:00:00:10 --alias NAS
lanip lab start pequeña
```

También se admiten `device delete`, `export --format json|csv`, `import`, `list`, `status` y `stop`.

## Seguridad y aislamiento

- No se envían paquetes, no se modifica ARP/DHCP/DNS/rutas ni interfaces.
- El inventario simulado vive separado de `devices.json`.
- Activar un escenario es explícito; `lab stop` vuelve al proveedor real.
- Los dispositivos llevan `SIMULATED` y opciones con escenario/proveedor/semilla.
- SSH, terminal, Radmin, apertura y escaneo profundo rechazan identidades simuladas.
- Las credenciales solo son el marcador `SIMULATED-ONLY`.

## Formato

El JSON usa `schemaVersion: 1` e incluye identidad, CIDR, perfil, semilla, reloj, dispositivos,
servicios/puertos y eventos. Las escrituras son atómicas y usan los locks comunes del Core.

Limitación actual: la vista TUI específica de escenarios queda desacoplada para una iteración
posterior; el CLI y la integración con `lanip list` son funcionales.
