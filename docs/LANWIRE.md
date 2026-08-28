# Integración LANWIRE

LANWIRE es el gestor de infraestructura física complementario de LANCTL. En
Windows se distribuye como `lanwire.exe` en el mismo directorio que
`LANCTL.exe` y `LANCTL-GUI.exe`.

## Ejecución

```powershell
lanctl lanwire
lanctl lanwire list
lanctl wire list
```

Sin argumentos se abre una consola independiente. Con argumentos, LANCTL espera
el resultado y devuelve el mismo código de salida. `--new-window` fuerza una
consola separada.

En desarrollo, el lanzador utiliza `lanwire.py` en la misma raíz que
`lanctl.py`. Las instalaciones finales buscan `lanwire.exe` junto a
`sys.executable`. Ambos son entradas independientes de un único proyecto.

## Contrato de datos

Antes de iniciar LANWIRE, LANCTL exporta su raíz resuelta en
`LANCTL_DATA_DIR`. También se conserva `LANCTL_DATA_SCOPE`. El marcador portable
debe contener exactamente `LANCTL-PORTABLE-V1`.

```text
<raíz compartida>/
├── database/devices.json       # inventario lógico LANCTL
├── monitoring/monitor.db       # monitorización LANCTL
└── physical/idf.db             # infraestructura física LANWIRE
```

La clave `physicalDatabase` de la configuración apunta por defecto a
`data/lc/physical/idf.db`. LANCTL solo conserva y muestra esta ruta; no abre la
base con `DeviceDatabase` ni mezcla sus tablas con otros almacenes.

## Compilación

`LANCTL.spec` analiza las dos entradas raíz, `lanctl.py` y `lanwire.py`, y
produce ambos ejecutables en una sola ejecución de PyInstaller. El script
`scripts/build-windows.ps1` exige los dos resultados y los incorpora al
instalador y al ZIP portable. Inno Setup lo
instala como parte del componente principal y lo elimina junto con los binarios,
pero conserva `%PROGRAMDATA%\LANCTL\physical` durante la desinstalación.
