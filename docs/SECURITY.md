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

## Fronteras de ejecución y acceso remoto

El runtime de plugins aislados transporta exclusivamente JSON mediante frames
de hasta 64 KiB. El padre valida la estructura, el handshake y el presupuesto de
llamadas; no deserializa objetos Python enviados por el plugin. La recepción se
separa del control de tiempo para que un frame incompleto no bloquee la activación
ni el watchdog. Esto conserva `activate(api)`, `api.log` y `deactivate`; la conexión
interna no es una API pública para plugins. Los audit hooks y los límites del
proceso siguen sin equivaler a un sandbox del sistema operativo para código
hostil, como se indica en README.

Cada activación recibe una concesión nueva para el API del Core. Se comprueban
los permisos persistidos y la confianza del editor en cada acceso; las
referencias retenidas de callbacks, funciones, checks y almacenes dejan de ser
válidas al revocar. El gestor global reconcilia también cambios externos cada
0,5 s. La limpieza externa ocurre fuera de los locks del registro y no bloquea
la interfaz indefinidamente; una limpieza pendiente impide reactivar el plugin.
Esto no termina hilos nativos arbitrarios del runtime `trusted` heredado ni
deshace operaciones ya iniciadas. Su estado expone `restartRequired` y conserva
ese aviso durante la vida del gestor. La migración de runtime cancelable sigue
en REF-P34-runtime; no se declara esa frontera resuelta por invalidar callbacks.

Los VLF requieren un UUID canónico y su workspace resuelto debe permanecer
dentro de la raíz configurada. Los checksums validan integridad, no confianza en
las rutas proporcionadas por el archivo. Los paquetes LCP se extraen y verifican
en staging dentro del filesystem de destino antes de intercambiar la instalación.

En remoto, `list` requiere `scan.run` porque realiza descubrimiento y actualiza
inventario. `viewer` conserva consultas como `search` y la API de inventario; los
destinos `--output`/`-o`, incluidos sus alias abreviados, no están disponibles para
ningún rol remoto. Cada operación vuelve a comprobar la cuenta y sus roles
persistidos; desactivación, caducidad, eliminación o rotación de autenticadores
invalidan el objeto autenticado anterior.

HTTPS filtra el origen de red antes de iniciar TLS y limita el handshake a un
worker con timeout. Los POST autenticados requieren un token CSRF presente y
válido. Las consultas SSH de Netmiko instalan la política de huella antes de abrir
la conexión y autenticar; la comprobación preliminar no sustituye esa validación.
