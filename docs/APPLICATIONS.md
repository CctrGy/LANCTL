# Aplicaciones paralelas de LANCTL

`LANCTL` es el orquestador común. Permite abrir las aplicaciones con `lanctl ip`,
`lanctl wire`, `lanctl rack` y `lanctl access`; los ejecutables independientes
usan los mismos datos y la misma versión de la suite.

## LANRACK

`LANRACK` consulta `physical/idf.db`, cuya propiedad sigue correspondiendo a
`LANWIRE`. Presenta únicamente registros de tipo rack y los elementos cuya
ubicación apunta a cada rack. Su primera versión es de solo lectura para evitar
que dos aplicaciones editen el cableado con reglas diferentes.

```powershell
lanrack list
lanrack show RK-00
lanrack --tui
lanctl rack --tui
```

## LANACCESS

`LANACCESS` administra el almacén cifrado DPAPI que ya utiliza `LANIP`. Lista
solo identificadores, elementos, protocolos y usuarios; nunca imprime las
contraseñas. Al eliminar una credencial también retira sus referencias del
inventario lógico.

```powershell
lanaccess list
lanaccess set SWITCH-CORE ssh --username operador
lanaccess delete cred_...
lanaccess --tui
lanctl access --tui
```

`LANIP` conserva las acciones operativas como abrir SSH. Para ello obtiene la
credencial mediante su referencia compartida, sin asumir la gestión del almacén.
