# Seguridad del proyecto

Las comprobaciones de cada cambio a `main` incluyen pruebas de integración y
cobertura de ramas, Ruff, Bandit, `pip check`, `pip-audit`, CodeQL y revisión
de dependencias. Dependabot revisa semanalmente paquetes Python y GitHub
Actions. Los workflows usan permisos mínimos y la publicación solo obtiene
`contents: write` dentro del trabajo que crea una release desde un tag.

## Excepción temporal de auditoría

`PYSEC-2026-3552` afecta exclusivamente a las funciones
`pkcs7_decrypt_der`, `pkcs7_decrypt_pem` y `pkcs7_decrypt_smime` de
cryptography anteriores a 50.0. LANCTL no importa ni ofrece esas funciones y no
procesa S/MIME/PKCS#7 cifrado, por lo que esa ruta no es alcanzable. La versión
estable 49 corrige los demás avisos detectados. CI ignora solamente este ID; la
excepción debe eliminarse al adoptar cryptography 50.0 estable.

`PYSEC-2026-2858` afecta a la firma RSA/SHA-1 permitida por Paramiko 4. LANCTL
deshabilita `ssh-rsa`, `ssh-dss` y los intercambios Diffie-Hellman SHA-1 tanto
en el servidor y en los perfiles cliente normales; su servidor usa una host
key Ed25519. El perfil Cisco S300 puede habilitar RSA/SHA-1 de forma explícita,
acotada al dispositivo y con huella fijada, para equipos heredados que no
negocian otra opción. Se mantiene Paramiko 4 porque Netmiko 4.7 declara
`paramiko<5`; esta excepción debe eliminarse cuando Netmiko sea compatible con
Paramiko 5.
