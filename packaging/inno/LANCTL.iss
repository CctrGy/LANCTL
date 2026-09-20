#define MyAppName "LANCTL"
#ifndef MyAppVersion
  #define MyAppVersion "0.3.1-beta.3"
#endif
#ifndef BuildRoot
  #define BuildRoot "..\..\dist"
#endif

[Setup]
AppId={{784B812A-7D24-493D-96DE-A62522792841}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={autopf}\LANCTL
DefaultGroupName=LANCTL
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist\release
OutputBaseFilename=LANCTL-{#MyAppVersion}-windows-x64-setup
Compression=lzma2/max
SolidCompression=yes
SetupIconFile=..\..\assets\lanctl-v3.ico
PrivilegesRequired=admin
UninstallDisplayIcon={app}\LANCTL.exe
ChangesEnvironment=yes
SetupLogging=yes

[Types]
Name: standard; Description: "Standard"
Name: monitor; Description: "Monitor node"
Name: custom; Description: "Custom"; Flags: iscustom

[Components]
Name: core; Description: "LANCTL application"; Types: standard monitor custom; Flags: fixed
Name: path; Description: "Add LANCTL to system PATH"; Types: standard monitor custom
Name: monitor; Description: "Monitor service"; Types: monitor custom

[Dirs]
; La raíz también hereda permisos de modificación para que cualquier estado
; futuro que todavía no tenga subcarpeta no quede bloqueado al usuario normal.
Name: "{commonappdata}\LANCTL"; Permissions: users-modify
Name: "{commonappdata}\LANCTL\config"; Permissions: users-modify
Name: "{commonappdata}\LANCTL\access"; Permissions: admins-full system-full
Name: "{commonappdata}\LANCTL\database"; Permissions: users-modify
Name: "{commonappdata}\LANCTL\logs"; Permissions: users-modify
Name: "{commonappdata}\LANCTL\monitoring"; Permissions: users-modify
Name: "{commonappdata}\LANCTL\physical"; Permissions: users-modify
Name: "{commonappdata}\LANCTL\plugins"; Permissions: admins-full system-full
Name: "{commonappdata}\LANCTL\projects"; Permissions: users-modify
Name: "{commonappdata}\LANCTL\automation"; Permissions: users-modify

[Files]
Source: "{#BuildRoot}\LANCTL.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanip.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanwire.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanmon.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanrack.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanaccess.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "..\..\docs\INSTALL.md"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "..\..\docs\ACCESS.md"; DestDir: "{app}"; Flags: ignoreversion; Components: core

[InstallDelete]
; Limpia launchers heredados que pudieron quedar al actualizar instalaciones
; anteriores a la separación actual entre raíz y aplicaciones.
Type: files; Name: "{app}\LANCTL-GUI.exe"
Type: files; Name: "{app}\landemo.exe"

[Icons]
Name: "{group}\LANCTL TUI"; Filename: "{app}\LANCTL.exe"; Parameters: "--tui"; WorkingDir: "{app}"
Name: "{group}\LANCTL CLI"; Filename: "{app}\LANCTL.exe"; Parameters: "--cli"; WorkingDir: "{app}"
Name: "{group}\LANIP"; Filename: "{app}\lanip.exe"; Parameters: "--tui"; WorkingDir: "{app}"
Name: "{group}\LANWIRE Physical"; Filename: "{app}\lanwire.exe"; WorkingDir: "{app}"
Name: "{group}\LANMON Monitor"; Filename: "{app}\lanmon.exe"; WorkingDir: "{app}"
Name: "{group}\LANRACK Viewer"; Filename: "{app}\lanrack.exe"; WorkingDir: "{app}"
Name: "{group}\LANACCESS Credentials"; Filename: "{app}\lanaccess.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\LANCTL TUI"; Filename: "{app}\LANCTL.exe"; Parameters: "--tui"; WorkingDir: "{app}"; Tasks: desktopicon

[Tasks]
Name: desktopicon; Description: "Crear acceso directo de LANCTL TUI en el escritorio"; Flags: unchecked

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}'); Components: path

[Run]
; Corta la herencia users-modify de la raíz para credenciales y código de plugins.
Filename: "{sys}\icacls.exe"; Parameters: """{commonappdata}\LANCTL\access"" /inheritance:r /grant:r ""*S-1-5-18:(OI)(CI)F"" ""*S-1-5-32-544:(OI)(CI)F"""; Flags: runhidden waituntilterminated
Filename: "{sys}\icacls.exe"; Parameters: """{commonappdata}\LANCTL\plugins"" /inheritance:r /grant:r ""*S-1-5-18:(OI)(CI)F"" ""*S-1-5-32-544:(OI)(CI)F"""; Flags: runhidden waituntilterminated
Filename: "{app}\LANCTL.exe"; Parameters: "monitor service install --yes"; Components: monitor; Flags: runhidden waituntilterminated; StatusMsg: "Instalando el servicio permanente LANCTL Monitor..."

[UninstallRun]
Filename: "{app}\LANCTL.exe"; Parameters: "monitor service uninstall --yes"; Flags: runhidden waituntilterminated; RunOnceId: "LANCTLMonitorService"

[Code]
function NeedsAddPath(Param: string): Boolean;
var Paths: string;
begin
  if not RegQueryStringValue(HKLM, 'SYSTEM\CurrentControlSet\Control\Session Manager\Environment', 'Path', Paths) then Paths := '';
  Result := Pos(';' + Uppercase(Param) + ';', ';' + Uppercase(Paths) + ';') = 0;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var Mode: string;
begin
  if CurStep = ssInstall then begin
    Mode := ExpandConstant('{param:MODE|standard}');
    if CompareText(Mode, 'monitor') = 0 then WizardSelectComponents('core,path,monitor');
  end;
end;
