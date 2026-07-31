# Capa gestionada de comandos Cisco

## Flujo

```text
entrada -> parser ALS -> CiscoPlanner -> CommandPlan -> política de riesgo
        -> CiscoAdapter -> salida normalizada
```

`CiscoPlanner` no conoce SSH ni Netmiko. `CommandPlan` contiene la identidad
estable ALS, endpoint actual, puerto lógico y nativo, riesgo y comandos que un
adaptador podría ejecutar. `FakeCiscoAdapter` es el único adaptador habilitado
en esta fase.

`CiscoExecutor` constituye una segunda barrera: no entrega planes de cambio al
adaptador si no llevan autorización explícita, incluso cuando el llamante no es
el CLI. En `dry-run` nunca invoca el adaptador.

## Perfiles

El archivo opcional `data/lc/cisco_profiles.json` tiene este formato:

```json
{
  "profiles": [
    {
      "id": "mi-switch-24",
      "model": "Cisco de ejemplo",
      "ports": [
        {
          "id": "port:7",
          "native": "GigabitEthernet1/7",
          "aliases": ["7", "p7", "x7"],
          "label": "NAS"
        }
      ]
    }
  ]
}
```

Todas las referencias se comparan sin distinguir mayúsculas. Una referencia
ambigua o inexistente se rechaza antes de crear el plan.

Las etiquetas específicas de un dispositivo se guardan en sus opciones
`cisco-cli.portLabels` y se superponen al perfil sin modificarlo:

```powershell
run switch SW port label x7 NAS
run switch SW --dry-run port show NAS status
run switch SW port unlabel NAS
```

## Catálogo y validación

Las consultas generales admitidas corresponden al catálogo de `show` definido
en `app/cisco/catalog.py`. Las acciones de puerto admiten:

- `show`: status, description, config, errors y vlan;
- `set`: description, speed y duplex;
- `enable`, `disable` y `reset`;
- alias históricos `start`, `stop`, `reset` y `xN`.

La velocidad se limita a `auto`, `10`, `100`, `1000` o `10000`; el dúplex a
`auto`, `half` o `full`. Los valores no admiten saltos de línea ni `;`, y las
descripciones del comando están limitadas a 64 caracteres.

## Seguridad

`READ_ONLY` no requiere confirmación. `CONFIG_CHANGE`,
`DESTRUCTIVE_OR_DISRUPTIVE` y `PERSIST_CONFIG` sí. `--dry-run` detiene el flujo
después de validar y mostrar el plan. Guardar `running-config` nunca forma parte
implícita de otro cambio.

La futura integración Netmiko deberá implementar la interfaz `CiscoAdapter`,
consumir únicamente objetos `CommandPlan` ya autorizados y conservar la
verificación de huella SSH existente. No deberá aceptar texto remoto libre.
