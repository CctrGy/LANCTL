# Catálogo de iconos de LANCTL

Este subsistema está destinado a la futura interfaz gráfica. No registra
comandos en CLI ni TUI.

## Almacenamiento

```text
data/lc/icons/
├── router.jpg
├── switch.jpg
└── icons.json
```

Los recursos deben ser JPEG completos de exactamente `125×125` píxeles. El
catálogo se regenera al iniciar LANCTL y contiene identificador, nombre,
archivo, dimensiones, SHA-256, categoría, etiquetas, propietario y fecha.
Archivos inválidos se anotan en `errors` sin impedir el inicio del programa.

## API para la GUI

```python
from app.assets.icons import get_icon_manager

icons = get_icon_manager()
icons.initialize()

entry = icons.register(
    "C:/imagenes/router.jpg",
    icon_id="device.router",
    name="Router",
    category="device",
    tags=("network", "gateway"),
)

path = icons.resolve("device.router")
available = icons.list(category="device")
```

No se deben leer rutas construidas manualmente desde la GUI; `resolve()` es la
fuente canónica.

## Extensión LCP

Un plugin puede aportar iconos mediante `api/api.map`:

```json
{
  "extensions": [
    {
      "id": "example.icon.router",
      "type": "icon",
      "specification": {
        "file": "assets/ui/router.jpg",
        "iconId": "device.router.example",
        "name": "Router Example",
        "category": "device",
        "tags": ["router", "network"]
      }
    }
  ]
}
```

Requiere `icon.register`. La ruta debe permanecer dentro del plugin. Al
desactivarlo, sus iconos desaparecen del catálogo sin borrar el paquete.
