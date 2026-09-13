# Seguridad del proyecto

Las comprobaciones de cada cambio a `main` incluyen pruebas de integración y
cobertura de ramas, Ruff, Bandit, `pip check`, `pip-audit`, CodeQL y revisión
de dependencias. Dependabot revisa semanalmente paquetes Python y GitHub
Actions. Los workflows usan permisos mínimos y la publicación solo obtiene
`contents: write` dentro del trabajo que crea una release desde un tag.

## Protección del repositorio

Los datos de ejecución, inventarios, proyectos VLF, credenciales, claves SSH,
logs, bases SQLite y artefactos compilados no forman parte del código fuente y
están excluidos mediante `.gitignore`. Antes de publicar cambios puede ejecutarse:

```console
python tools/check_repository_hygiene.py
```

La integración continua ejecuta la misma comprobación y rechaza rutas locales
delicadas y firmas de secretos de alta confianza. Esto complementa, pero no
sustituye, la rotación inmediata de cualquier credencial que llegue a publicarse.

## Auditoría de dependencias

LANCTL utiliza Paramiko 5 y cryptography 50. Las excepciones temporales de las
versiones anteriores se han eliminado: CI ejecuta `pip-audit --strict` sin
ignorar identificadores de vulnerabilidad. Los perfiles heredados continúan
requiriendo activación explícita y una huella fijada al dispositivo.
