# Verificación de LANCTL 0.3.0-beta.1

Fecha: 2026-08-01

## Resultado

- Elementos recurrentes: catálogo y comandos verificados.
- Suite completa: 211 pruebas superadas.
- Superficies: command y CLI ejecutados sobre el EXE; TUI iniciada y estable;
  GUI iniciada, enfocada y cerrada normalmente.
- Versiones: `app`, `pyproject.toml`, README y recursos de versión de Windows
  sincronizados con `0.3.0-beta.1` (`0.3.0.1` para `FileVersion`).
- VLF/LCP: contratos de compatibilidad 0.3 documentados; LCP rechaza schemas
  futuros y VLF mantiene la verificación estricta de formato `1.0`.
- PyInstaller: compilación one-file completada con GUI, HTML/CSS/JS, iconos,
  catálogo recurrente y plugin de tema integrado.
- Instalación limpia: el EXE crea `data/lc`, registros de idioma/iconos/plugins
  y los plugins integrados `lanctl.example.network-summary` y
  `lanctl.theme.default`.
- Actualización: una instalación previa conservó sin cambios de hash
  `.config`, `devices.json` y `groups.json`, y el inventario siguió siendo
  consultable.

## Artefacto verificado

- Archivo: `dist/LANCTL.exe`
- SHA-256: `A3CE40D09949269204EB0046E5FA8B963D9699502E7E8F2954E89C30A1DF2D78`
- Tamaño: 22,340,993 bytes
- `ProductVersion`: `0.3.0-beta.1`
- `FileVersion`: `0.3.0.1`

Los plugins externos trusted `lanctl.analysis.mac-vendor` y
`lanctl.discovery.mdns-ssdp` se distribuyen como LCP separados y no se activan
automáticamente en instalaciones limpias. Esto mantiene el requisito de
consentimiento explícito para permisos y `--trust`.

## Observaciones del build

Las advertencias de PyInstaller corresponden a backends opcionales o a
módulos exclusivos de otros sistemas operativos. La GUI Windows fue arrancada
desde el ejecutable compilado, por lo que esas ausencias no bloquean esta
distribución.
