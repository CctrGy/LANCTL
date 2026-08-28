# Errores estructurados

LANCTL representa los fallos nuevos mediante `ErrorEvent`, con nivel, origen jerárquico,
código estable, mensaje, recuperabilidad, contexto redactado y un identificador de
correlación. `ErrorManager.emit()` permite decidir de forma independiente si el error
se muestra (`print_output`) y si interrumpe la tarea (`break_execution`). Los errores
que interrumpen se muestran mediante su `repr`, útil para soporte y diagnóstico.

```python
from lanctl.core.errors import errors

errors.emit(
    level=46,
    origin="LANCTL.Network.Scanner.TCP",
    code="NETWORK.SCAN.TIMEOUT",
    message="El host agotó el tiempo de espera",
    details={"host": host},
    print_output=True,
    break_execution=False,
)
```

Los plugins disponen de `api.errors.emit(...)` y `api.errors.interpolate(...)`. Su
origen queda confinado automáticamente a `Plugin.<plugin-id>.*`; una interrupción del
plugin detiene únicamente su manejador y el bus de eventos continúa aislado.

La severidad utiliza toda la escala `1..59`. Los valores `10`, `20`, `30`, `40` y
`50` son referencias DEBUG/INFO/WARNING/ERROR/CRITICAL, pero los errores concretos
pueden usar valores intermedios. El `errorId` estable tiene el formato `0eXXXXXXXX`;
el UUID de correlación sigue identificando una ocurrencia concreta.

`errorLogLevel` controla el umbral persistente del log y vale `20` por defecto.
Los diagnósticos `1..19` nunca se imprimen automáticamente y sólo se escriben cuando
el umbral configurado los incluye:

```console
lanctl settings --error-log-level 10
```

Los fallbacks que pueden repetirse aceptan `once_key`. El gestor conserva la primera
entrada por proceso y evita inundar el registro con el mismo diagnóstico:

```python
errors.emit(
    level=8,
    origin="LANCTL.Config.Load.Defaults",
    code="CONFIG.DEFAULTS.USED",
    message="Se usan valores predeterminados",
    print_output=False,
    once_key="config.defaults.missing",
)
```

El catálogo `errorList.txt` incluye `raise`, diagnósticos estructurados, salidas con
error, retornos inequívocos de fallo y llamadas heredadas a `print_error`. No incluye
automáticamente cada `False` o `None`, porque suelen representar resultados normales
como puerto cerrado, elemento no encontrado o cancelación voluntaria.

Los IDs se calculan usando módulo, función, clase de punto y firma semántica. La línea
sólo es metadato, por lo que añadir líneas en blanco no cambia el identificador.

```python
try:
    discover()
except Exception as error:
    api.errors.interpolate(
        error,
        origin="Discovery.SSDP",
        code="PLUGIN.DISCOVERY.FAILED",
        break_execution=True,
        print_output=False,
    )
```
