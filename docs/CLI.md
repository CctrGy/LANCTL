# Referencia operativa del CLI

Todos los comandos admiten `-h`, `--help` y `/?`. `list` y `recurrent` ofrecen
`table`, `json`, `csv`, `html`, `xml` y `yaml`. Usa `--output` para escritura
atómica a archivo.

## Códigos de salida

| Código | Significado |
| --- | --- |
| `0` | Operación completada |
| `1` | Resultado negativo propio del comando |
| `2` | Argumento, configuración, E/S o estado inválido |
| `130` | Cancelación mediante teclado |

Los comandos remotos están permitidos por lista cerrada. Las operaciones de
borrado requieren `system.destructive`, concedido únicamente al rol
`administrator`. Para automatización, prefiere JSON/YAML y comprueba siempre el
código de salida antes de consumir el resultado.

Las familias principales son `list`, `scan`, `ping`, `element`, `group`,
`project`, `plugin`, `monitor`, `access`, `history`, `database`, `settings`,
`credential`, `protocol`, `smb`, `switch`, `wol`, `language` y `error`.
