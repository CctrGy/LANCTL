# Recuperación y solución de problemas

1. Ejecuta `lanctl database --diagnose` y conserva la salida.
2. Consulta un identificador mostrado con `lanctl error 0eXXXXXXXX`.
3. Revisa `logs/` sin publicar credenciales ni la carpeta `access/`.
4. Si falla un plugin, inicia con `pluginSafeMode: true`, revoca permisos o
   desactívalo.
5. Verifica un LCP con `lanctl plugin verify ARCHIVO.lcp` antes de instalarlo.
6. Verifica una copia de datos con `lanctl database --verify ARCHIVO.zip`.

No reemplaces un JSON corrupto por una copia sin validarla. No ejecutes dos
versiones incompatibles contra la misma raíz. En acceso remoto, comprueba que
el bind pertenece a la LAN, que el CIDR es correcto y que el ámbito `user` o
`service` coincide con el almacén de usuarios.

Para problemas del instalador, conserva el log de Inno Setup y prueba en una
máquina virtual limpia. La desinstalación no debe borrar `ProgramData\LANCTL`;
haz una exportación verificada antes de una actualización importante.
