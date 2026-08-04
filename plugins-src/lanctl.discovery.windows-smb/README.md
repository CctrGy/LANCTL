# Windows SMB Discovery

Plugin `trusted` para Windows. Usa TCP/445, `NetServerGetInfo`, `NetShareEnum`, `WNetAddConnection2`, `WNetCancelConnection2`, `ShellExecute` y `AddPrinterConnection`; no habilita SMB1 ni cambia políticas.

CLI: `smb scan [SERVIDOR]`, `smb SERVIDOR [info|shares|printers|status|connect|disconnect]`, `smb SERVIDOR open RECURSO`, `smb SERVIDOR printer IMPRESORA [open|queue|connect]`, `smb workgroups`. Use `--include-system`, `--anonymous`, `--dry-run`, `--yes` y `--json` cuando corresponda.

Las observaciones se guardan separadas del inventario. Las contraseñas permanecen en CredentialStore/DPAPI; Windows puede rechazar una conexión si ya existe otra sesión con credenciales distintas.
