# Herramientas auxiliares de desarrollo

Estas herramientas ayudan a revisar LANCTL, pero no forman parte del programa
ni de sus instaladores. Se instalan fuera del repositorio. Sus configuraciones
reproducibles y documentos de arquitectura sí se versionan.

## Qué se guarda en Git

- `.madgerc`, `sonar-project.properties` y workflows de GitHub Actions.
- `docs/architecture/workspace.dsl` y los ADR de `docs/adr/`.
- Scripts propios necesarios para repetir una comprobación.

## Qué se ignora

- `node_modules/`, `.scannerwork/`, `.sonar/` y `.structurizr/`.
- `.tool-cache/`, `.tool-reports/` y resultados locales de análisis.
- Tokens, claves, servidores descargados y binarios de las herramientas.

## Madge y Graphviz

Madge analiza las dependencias JavaScript de la GUI. Está instalado globalmente
y Graphviz permite generar diagramas.

```powershell
madge --circular gui/app.js
New-Item -ItemType Directory -Force .tool-reports
madge --image .tool-reports/madge-gui.svg gui/app.js
```

Madge no analiza Python. Las dependencias del Core se protegen mediante las
pruebas, Ruff y las reglas de arquitectura del repositorio.

## SonarScanner y SonarQube

`sonar-project.properties` contiene rutas y exclusiones, nunca credenciales.
Primero se genera la cobertura y después se envía el análisis a un servidor
SonarQube o SonarCloud configurado por variables de entorno:

```powershell
python -m coverage run --branch --source=src -m pytest -p no:cacheprovider
python -m coverage xml -o coverage.xml
$env:SONAR_HOST_URL = "https://servidor-sonar.example"
$env:SONAR_TOKEN = "TOKEN_TEMPORAL"
sonar-scanner
Remove-Item Env:SONAR_TOKEN
```

SonarScanner está instalado, pero no se ha instalado un servidor SonarQube ni
se ha creado un token. El análisis no puede enviarse hasta elegir ese destino.

## Structurizr

El modelo C4 inicial está en `docs/architecture/workspace.dsl`. El antiguo
Structurizr CLI fue archivado en 2026, por lo que no se incorpora su binario al
proyecto. El DSL puede abrirse en el playground oficial o procesarse con las
herramientas consolidadas actuales de Structurizr cuando se disponga del
runtime elegido. Las carpetas de estado local quedan ignoradas.

## ADR

Los ADR son documentación permanente. `adr-tools` está instalado fuera del
repositorio y se utiliza desde Git Bash:

```bash
adr list
adr new "Título de la decisión"
```

El directorio de decisiones es `docs/adr/`. Revisa siempre el archivo generado
antes de guardarlo en Git.

## GitHub Actions

No se instala localmente. GitHub interpreta los YAML versionados de
`.github/workflows/` y ejecuta CI, seguridad y releases en sus runners. Los
artefactos temporales de cada ejecución permanecen en GitHub y no se añaden al
repositorio.
