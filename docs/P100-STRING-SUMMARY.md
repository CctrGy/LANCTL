# P100 — Inventario estático de cadenas

Generado con `python3 tools/generate_string_inventory.py`. No importa ni ejecuta LANCTL.

Archivos examinados: **368**. Entradas: **31902**. Valores de texto distintos: **11535**.

Son ocurrencias conservadoras de literales, no un recuento de traducciones necesarias ni una certificación de cobertura funcional.

| Propietario | Interfaz de origen | Ocurrencias |
|---|---|---:|
| INSTALLER | INSTALLER | 1806 |
| LANACCESS | CLI | 1 |
| LANACCESS | CLI/TUI | 316 |
| LANACCESS | GUI | 60 |
| LANACCESS | SHARED | 1375 |
| LANCTL | CLI | 134 |
| LANCTL | CLI/TUI | 8 |
| LANCTL | GUI | 1405 |
| LANCTL | SHARED | 173 |
| LANIP | CLI | 4122 |
| LANIP | GUI | 1815 |
| LANIP | SHARED | 1268 |
| LANIP | TUI | 2636 |
| LANMON | CLI | 51 |
| LANMON | CLI/TUI | 31 |
| LANMON | GUI | 228 |
| LANMON | SHARED | 1124 |
| LANMON | TUI | 58 |
| LANRACK | CLI | 1 |
| LANRACK | CLI/TUI | 156 |
| LANRACK | GUI | 197 |
| LANRACK | SHARED | 275 |
| LANWIRE | CLI | 443 |
| LANWIRE | GUI | 894 |
| LANWIRE | SHARED | 956 |
| LANWIRE | TUI | 1675 |
| SHARED | CATALOG | 154 |
| SHARED | CLI | 108 |
| SHARED | CLI/TUI | 54 |
| SHARED | GUI | 2339 |
| SHARED | GUI:PROTOTYPE | 699 |
| SHARED | SHARED | 6786 |
| SHARED | TUI | 48 |
| lanctl.analysis.mac-vendor | PLUGIN | 108 |
| lanctl.discovery.mdns-ssdp | PLUGIN | 38 |
| lanctl.discovery.windows-smb | PLUGIN | 151 |
| lanctl.integration.terminal | PLUGIN | 142 |
| lanctl.lab.network-emulator | PLUGIN | 36 |
| lanctl.network.wol | PLUGIN | 31 |

## Clasificación inicial

| Clase | Ocurrencias |
|---|---:|
| CATALOG | 134 |
| KEY_REFERENCE | 297 |
| REVIEW | 28532 |
| REVIEW_EMBEDDED_CODE | 2 |
| TECHNICAL_ERROR_REVIEW_PRESENTATION | 1444 |
| TECHNICAL_LOG | 3 |
| UI_CANDIDATE | 1490 |

Las clases son indicios automáticos: `UI_CANDIDATE` también puede contener datos técnicos; `REVIEW` conserva valores sin decidir su destino; los errores requieren revisar cómo llegan a pantalla. `KEY_REFERENCE` identifica referencias, no traducciones. La propiedad SHARED no duplica entradas entre consumidores.
