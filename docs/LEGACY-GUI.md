# GUI heredada congelada

La GUI se conserva únicamente como referencia mientras el desarrollo se centra
en CLI y TUI. No recibe nuevas funciones, no participa en la batería ordinaria
de pruebas y no se incluye en los ejecutables, el ZIP portable, el instalador ni
los accesos directos de Windows.

El arranque `lanctl` sin argumentos abre el TUI. Para probar la GUI desde el
código fuente de forma explícita:

```powershell
python -m pip install -e ".[gui]"
$env:LANCTL_ENABLE_LEGACY_GUI = "1"
lanctl --gui
```

Sus pruebas se ejecutan separadamente con:

```powershell
python -m pytest -m legacy_gui
```

Este mecanismo no constituye soporte de producción y puede retirarse cuando se
diseñe una GUI nueva sobre los contratos estabilizados del núcleo.
