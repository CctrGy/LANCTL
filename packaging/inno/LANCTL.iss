#define MyAppName "LANCTL GUI experimental (NO ESTABLE)"
#ifndef MyAppVersion
  #define MyAppVersion "0.3.4-alpha.1"
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
SetupIconFile=..\..\assets\launcher-icons\lanctl.ico
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
Name: plugins; Description: "Plugins opcionales (todos, ninguno o selección individual)"; Types: standard monitor custom
Name: plugins\example; Description: "Ejemplo: resumen de inventario"; Types: standard monitor custom
Name: plugins\vendor; Description: "Fabricantes MAC (requiere firma autorizada para activar)"; Types: standard monitor custom
Name: plugins\mdns; Description: "Descubrimiento mDNS/SSDP (requiere firma autorizada para activar)"; Types: standard monitor custom
Name: plugins\smb; Description: "Descubrimiento Windows/SMB (requiere firma autorizada para activar)"; Types: standard monitor custom
Name: plugins\wol; Description: "Wake-on-LAN (requiere firma autorizada para activar)"; Types: standard monitor custom
Name: plugins\lab; Description: "Emulador de red"; Types: standard monitor custom

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
Source: "..\..\assets\launcher-icons\terminal.ico"; DestDir: "{app}\assets\launcher-icons"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\LANCTL.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanip.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanwire.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanmon.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanrack.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanaccess.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "..\..\docs\INSTALL.md"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "..\..\docs\ACCESS.md"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "..\..\packaging\clink\lanctl.lua"; DestDir: "{app}\clink"; Flags: ignoreversion; Components: core
Source: "..\..\packaging\clink\README.md"; DestDir: "{app}\clink"; Flags: ignoreversion; Components: core

[InstallDelete]
; Limpia launchers heredados que pudieron quedar al actualizar instalaciones
; anteriores a la separación actual entre raíz y aplicaciones.
Type: files; Name: "{app}\LANCTL-GUI.exe"
Type: files; Name: "{app}\landemo.exe"

[Icons]
Name: "{group}\LANCTL GUI"; Filename: "{app}\LANCTL.exe"; Parameters: "--gui"; WorkingDir: "{app}"
Name: "{group}\LANWIRE GUI"; Filename: "{app}\lanwire.exe"; Parameters: "--gui"; WorkingDir: "{app}"
Name: "{group}\LANRACK GUI"; Filename: "{app}\lanrack.exe"; Parameters: "--gui"; WorkingDir: "{app}"
Name: "{group}\LANACCESS GUI"; Filename: "{app}\lanaccess.exe"; Parameters: "--gui"; WorkingDir: "{app}"
Name: "{group}\LANMON GUI"; Filename: "{app}\lanmon.exe"; Parameters: "--gui"; WorkingDir: "{app}"
Name: "{group}\LANCTL TUI"; Filename: "{app}\LANCTL.exe"; Parameters: "--tui"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANCTL CLI"; Filename: "{app}\LANCTL.exe"; Parameters: "--cli"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANIP"; Filename: "{app}\lanip.exe"; Parameters: "--tui"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANIP GUI"; Filename: "{app}\lanip.exe"; Parameters: "--gui"; WorkingDir: "{app}"; Tasks: ipgui
Name: "{group}\LANWIRE Physical"; Filename: "{app}\lanwire.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANMON Monitor"; Filename: "{app}\lanmon.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANMON Events"; Filename: "{app}\lanmon.exe"; Parameters: "--tui"; WorkingDir: "{app}"; Tasks: eventviewer; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANACCESS Administrator (UAC)"; Filename: "{app}\LANCTL.exe"; Parameters: "--admin lanaccess --tui"; WorkingDir: "{app}"; Tasks: accessadmin; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANRACK Viewer"; Filename: "{app}\lanrack.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANACCESS Credentials"; Filename: "{app}\lanaccess.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{autodesktop}\LANCTL TUI"; Filename: "{app}\LANCTL.exe"; Parameters: "--tui"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\assets\launcher-icons\terminal.ico"

[Tasks]
Name: ipgui; Description: "Crear acceso directo a la interfaz gráfica de LANIP (requiere WebView2)"; Flags: unchecked
Name: desktopicon; Description: "Crear acceso directo de LANCTL TUI en el escritorio"; Flags: unchecked
Name: eventviewer; Description: "Crear acceso directo al visor de eventos LANMON"; Flags: unchecked
Name: accessadmin; Description: "Crear acceso LANACCESS administrativo (solicita UAC al abrir; no eleva el resto de programas)"; Flags: unchecked
Name: firstscan; Description: "Al abrir LANIP al finalizar, preparar el primer escaneo con confirmación del rango (rutas del sistema)"; Flags: unchecked

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}'); Components: path

[Run]
; Corta la herencia users-modify de la raíz para credenciales y código de plugins.
Filename: "{sys}\icacls.exe"; Parameters: """{commonappdata}\LANCTL\access"" /inheritance:r /grant:r ""*S-1-5-18:(OI)(CI)F"" ""*S-1-5-32-544:(OI)(CI)F"""; Flags: runhidden waituntilterminated
Filename: "{sys}\icacls.exe"; Parameters: """{commonappdata}\LANCTL\plugins"" /inheritance:r /grant:r ""*S-1-5-18:(OI)(CI)F"" ""*S-1-5-32-544:(OI)(CI)F"""; Flags: runhidden waituntilterminated
Filename: "{app}\LANCTL.exe"; Parameters: "setup-defaults --theme {code:GetInitialTheme} --plugins {code:GetPluginSelection}"; Flags: runhidden waituntilterminated; StatusMsg: "Preparando preferencias y plugins sin activarlos; conservando elecciones existentes..."
Filename: "{app}\LANCTL.exe"; Parameters: "completions install"; Flags: runhidden waituntilterminated runasoriginaluser; StatusMsg: "Registrando el completado Clink del usuario, si está disponible..."
Filename: "{app}\LANCTL.exe"; Parameters: "monitor service install --yes"; Components: monitor; Flags: runhidden waituntilterminated; StatusMsg: "Instalando el servicio permanente LANCTL Monitor..."
Filename: "{app}\lanaccess.exe"; Parameters: "--tui"; Description: "Abrir LANACCESS para configurar credenciales del usuario (sin guardarlas en el instalador)"; Flags: postinstall unchecked skipifsilent runasoriginaluser
Filename: "{app}\LANCTL.exe"; Parameters: "{code:GetLanipArguments}"; Description: "Abrir LANIP (y preparar la confirmación del primer escaneo si se seleccionó)"; Flags: postinstall unchecked skipifsilent runasoriginaluser runhidden

[UninstallRun]
Filename: "{app}\LANCTL.exe"; Parameters: "completions uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "LANCTLClinkCurrentUser"
Filename: "{app}\LANCTL.exe"; Parameters: "monitor service uninstall --yes"; Flags: runhidden waituntilterminated; RunOnceId: "LANCTLMonitorService"

[Code]
var
  ThemePage: TInputOptionWizardPage;
  ThemePreview: TPanel;
  ThemeAccent: TPanel;

function GetInitialTheme(Param: String): String;
begin
  case ThemePage.SelectedValueIndex of
    1: Result := 'midnight';
    2: Result := 'forest';
    3: Result := 'violet';
    4: Result := 'light';
  else Result := 'graphite';
  end;
end;

procedure UpdateThemePreview(Sender: TObject);
begin
  ThemePreview.Font.Color := $f4efe9;
  case ThemePage.SelectedValueIndex of
    1: begin ThemePreview.Color := $221507; ThemeAccent.Color := $e8a925; end;
    2: begin ThemePreview.Color := $181b10; ThemeAccent.Color := $81db8c; end;
    3: begin ThemePreview.Color := $221619; ThemeAccent.Color := $ff9cbc; end;
    4: begin ThemePreview.Color := $f8f5f2; ThemeAccent.Color := $007347; ThemePreview.Font.Color := $2b2118; end;
  else begin ThemePreview.Color := $1c1815; ThemeAccent.Color := $26efb2; end;
  end;
end;

procedure InitializeWizard;
begin
  ThemePage := CreateInputOptionPage(wpSelectComponents, 'Apariencia inicial',
    'Elige un tema para el primer inicio',
    'Las actualizaciones conservan el tema y los plugins elegidos previamente. El tema base siempre se incluye.', True, False);
  ThemePage.Add('Grafito');
  ThemePage.Add('Azul noche');
  ThemePage.Add('Bosque');
  ThemePage.Add('Violeta');
  ThemePage.Add('Claro');
  ThemePage.SelectedValueIndex := 0;
  ThemePage.CheckListBox.Height := ScaleY(120);
  ThemePage.CheckListBox.OnClickCheck := @UpdateThemePreview;
  ThemePreview := TPanel.Create(WizardForm);
  ThemePreview.Parent := ThemePage.Surface;
  ThemePreview.SetBounds(0, ScaleY(165), ThemePage.SurfaceWidth, ScaleY(55));
  ThemePreview.Caption := 'LANCTL · Vista previa de fondo y acento';
  ThemeAccent := TPanel.Create(WizardForm);
  ThemeAccent.Parent := ThemePage.Surface;
  ThemeAccent.SetBounds(0, ScaleY(220), ThemePage.SurfaceWidth, ScaleY(8));
  UpdateThemePreview(nil);
end;

procedure AddSelectedPlugin(var Selection: String; Component, PluginId: String);
begin
  if WizardIsComponentSelected(Component) then begin
    if Selection <> '' then Selection := Selection + ',';
    Selection := Selection + PluginId;
  end;
end;

function GetPluginSelection(Param: String): String;
begin
  Result := '';
  AddSelectedPlugin(Result, 'plugins\example', 'lanctl.example.network-summary');
  AddSelectedPlugin(Result, 'plugins\vendor', 'lanctl.analysis.mac-vendor');
  AddSelectedPlugin(Result, 'plugins\mdns', 'lanctl.discovery.mdns-ssdp');
  AddSelectedPlugin(Result, 'plugins\smb', 'lanctl.discovery.windows-smb');
  AddSelectedPlugin(Result, 'plugins\wol', 'lanctl.network.wol');
  AddSelectedPlugin(Result, 'plugins\lab', 'lanctl.lab.network-emulator');
  if Result = '' then Result := 'none';
end;

function GetLanipArguments(Param: String): String;
begin
  Result := 'post-install';
  if WizardIsTaskSelected('firstscan') then Result := Result + ' --first-scan';
end;

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
