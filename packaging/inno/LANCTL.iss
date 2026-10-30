#define MyAppName "LANCTL GUI experimental (NO ESTABLE)"
#ifndef MyAppVersion
  #define MyAppVersion "0.3.4-alpha.2"
#endif
#ifndef BuildRoot
  #define BuildRoot "..\..\dist"
#endif

[Setup]
AppId={{784B812A-7D24-493D-96DE-A62522792841}
AppName={cm:AppName}
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
WizardSizePercent=130,140
ShowLanguageDialog=yes
UsePreviousLanguage=yes
UsePreviousTasks=yes

[Languages]
Name: en; MessagesFile: "compiler:Default.isl"
Name: es; MessagesFile: "compiler:Languages\Spanish.isl"

#include "messages.iss"

[Types]
Name: standard; Description: "{cm:TypeStandard}"
Name: monitor; Description: "{cm:TypeMonitor}"
Name: custom; Description: "{cm:TypeCustom}"; Flags: iscustom

[Components]
Name: core; Description: "LANCTL application"; Types: standard monitor custom; Flags: fixed
Name: path; Description: "Add LANCTL to system PATH"; Types: standard monitor custom
Name: monitor; Description: "{cm:Monitor}"; Types: standard monitor custom
Name: plugins; Description: "{cm:Plugins}"; Types: standard monitor custom
Name: plugins\example; Description: "{cm:Example}"; Types: standard monitor custom
Name: plugins\vendor; Description: "{cm:Vendor}"; Types: standard monitor custom
Name: plugins\mdns; Description: "{cm:Mdns}"; Types: standard monitor custom
Name: plugins\smb; Description: "{cm:Smb}"; Types: standard monitor custom
Name: plugins\wol; Description: "{cm:Wol}"; Types: standard monitor custom
Name: plugins\lab; Description: "{cm:Lab}"; Types: standard monitor custom

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
Source: "theme-previews\*.bmp"; Flags: dontcopy
Source: "..\..\assets\launcher-icons\terminal.ico"; DestDir: "{app}\assets\launcher-icons"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\LANCTL.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
Source: "{#BuildRoot}\lanctl-window.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: core
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
Name: "{group}\LANCTL GUI"; Filename: "{app}\lanctl-window.exe"; Parameters: "lanctl"; WorkingDir: "{app}"; IconFilename: "{app}\LANCTL.exe"
Name: "{group}\LANWIRE GUI"; Filename: "{app}\lanctl-window.exe"; Parameters: "lanwire"; WorkingDir: "{app}"; IconFilename: "{app}\lanwire.exe"
Name: "{group}\LANRACK GUI"; Filename: "{app}\lanctl-window.exe"; Parameters: "lanrack"; WorkingDir: "{app}"; IconFilename: "{app}\lanrack.exe"
Name: "{group}\LANACCESS GUI"; Filename: "{app}\lanctl-window.exe"; Parameters: "lanaccess"; WorkingDir: "{app}"; IconFilename: "{app}\lanaccess.exe"
Name: "{group}\LANMON GUI"; Filename: "{app}\lanctl-window.exe"; Parameters: "lanmon"; WorkingDir: "{app}"; IconFilename: "{app}\lanmon.exe"
Name: "{group}\LANCTL TUI"; Filename: "{app}\LANCTL.exe"; Parameters: "--tui"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANCTL CLI"; Filename: "{app}\LANCTL.exe"; Parameters: "--cli"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANIP"; Filename: "{app}\lanip.exe"; Parameters: "--tui"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANIP GUI"; Filename: "{app}\lanctl-window.exe"; Parameters: "lanip"; WorkingDir: "{app}"; Tasks: ipgui; IconFilename: "{app}\lanip.exe"
Name: "{group}\LANWIRE {cm:Physical}"; Filename: "{app}\lanwire.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANMON {cm:MonitorShortcut}"; Filename: "{app}\lanmon.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANMON {cm:MonitorEvents}"; Filename: "{app}\lanmon.exe"; Parameters: "--tui"; WorkingDir: "{app}"; Tasks: eventviewer; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANACCESS {cm:Administrator}"; Filename: "{app}\LANCTL.exe"; Parameters: "--admin lanaccess --tui"; WorkingDir: "{app}"; Tasks: accessadmin; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANRACK {cm:Viewer}"; Filename: "{app}\lanrack.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{group}\LANACCESS {cm:Credentials}"; Filename: "{app}\lanaccess.exe"; WorkingDir: "{app}"; IconFilename: "{app}\assets\launcher-icons\terminal.ico"
Name: "{autodesktop}\LANCTL TUI"; Filename: "{app}\LANCTL.exe"; Parameters: "--tui"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\assets\launcher-icons\terminal.ico"

[Tasks]
Name: clink; Description: "{cm:Clink}"; GroupDescription: "{cm:ClinkHelp}"
Name: ipgui; Description: "{cm:IpGui}"; Flags: unchecked
Name: desktopicon; Description: "{cm:Desktop}"; Flags: unchecked
Name: eventviewer; Description: "{cm:EventViewer}"; Flags: unchecked
Name: accessadmin; Description: "{cm:AccessAdmin}"; Flags: unchecked
Name: remoteaccount; Description: "{cm:RemoteAccount}"; Flags: checkedonce
Name: firstscan; Description: "{cm:FirstScan}"; Flags: unchecked

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}'); Components: path

[Run]
; Corta la herencia users-modify de la raíz para credenciales y código de plugins.
Filename: "{sys}\icacls.exe"; Parameters: """{commonappdata}\LANCTL\access"" /inheritance:r /grant:r ""*S-1-5-18:(OI)(CI)F"" ""*S-1-5-32-544:(OI)(CI)F"""; Flags: runhidden waituntilterminated
Filename: "{sys}\icacls.exe"; Parameters: """{commonappdata}\LANCTL\plugins"" /inheritance:r /grant:r ""*S-1-5-18:(OI)(CI)F"" ""*S-1-5-32-544:(OI)(CI)F"""; Flags: runhidden waituntilterminated; AfterInstall: ConfigureInitialPreferences
Filename: "{app}\lanaccess.exe"; Parameters: "remote-setup"; Tasks: remoteaccount; Flags: runhidden waituntilterminated skipifsilent; StatusMsg: "{cm:RemoteStatus}"
Filename: "{app}\LANCTL.exe"; Parameters: "completions install"; Tasks: clink; Flags: runhidden waituntilterminated runasoriginaluser; StatusMsg: "{cm:ClinkStatus}"
Filename: "{app}\LANCTL.exe"; Parameters: "monitor service install --yes"; Components: monitor; Flags: runhidden waituntilterminated; StatusMsg: "{cm:MonitorStatus}"
Filename: "{app}\lanaccess.exe"; Parameters: "--tui"; Description: "{cm:OpenAccess}"; Flags: postinstall unchecked skipifsilent runasoriginaluser
Filename: "{app}\LANCTL.exe"; Parameters: "{code:GetLanipArguments}"; Description: "{cm:OpenIp}"; Flags: postinstall unchecked skipifsilent runasoriginaluser runhidden

Filename: "{app}\LANCTL.exe"; Parameters: "completions uninstall"; Check: not WizardIsTaskSelected('clink'); Flags: runhidden waituntilterminated runasoriginaluser; StatusMsg: "{cm:ClinkRemoveStatus}"

[UninstallRun]
Filename: "{app}\LANCTL.exe"; Parameters: "completions uninstall"; Flags: runhidden waituntilterminated; RunOnceId: "LANCTLClinkCurrentUser"
Filename: "{app}\LANCTL.exe"; Parameters: "monitor service uninstall --yes"; Flags: runhidden waituntilterminated; RunOnceId: "LANCTLMonitorService"

[Code]
var
  ThemePage: TInputOptionWizardPage;
  ThemePreview: TBitmapImage;
  MonitorExplanation: TNewStaticText;
  ProgramLanguagePage: TWizardPage;
  ProgramLanguageCombo: TNewComboBox;
  ProgramLanguageCodes: TStringList;
  ChangeProgramLanguage: TNewCheckBox;
  ProgramLanguageHelp: TNewStaticText;

#include "program-languages.iss"

function GetProgramLanguage(Param: String): String;
begin
  Result := ProgramLanguageCodes[ProgramLanguageCombo.ItemIndex];
end;


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
  ThemePreview.Bitmap.LoadFromFile(ExpandConstant('{tmp}\') + GetInitialTheme('') + '.bmp');
end;

procedure InitializeWizard;
var Requested, Previous, ChangeRequested, Tasks: String;
  Index: Integer;
  TaskOverride: Boolean;
begin
  { Older versions always attempted Clink registration. Preserve that default
    on the first migration, unless the command line explicitly chooses tasks. }
  TaskOverride := False;
  for Index := 1 to ParamCount do
    if (Pos('/tasks=', Lowercase(ParamStr(Index))) = 1) or
       (Pos('/mergetasks=', Lowercase(ParamStr(Index))) = 1) then TaskOverride := True;
  if (GetPreviousData('ClinkChoiceVersion', '') = '') and not TaskOverride then begin
    Tasks := WizardSelectedTasks(False);
    if Tasks <> '' then Tasks := Tasks + ',';
    WizardSelectTasks(Tasks + 'clink');
  end;
  MonitorExplanation := TNewStaticText.Create(WizardForm);
  MonitorExplanation.Parent := WizardForm.ComponentsList.Parent;
  MonitorExplanation.AutoSize := False;
  MonitorExplanation.WordWrap := True;
  MonitorExplanation.Width := WizardForm.ComponentsList.Width;
  MonitorExplanation.Caption := CustomMessage('MonitorExplanation');
  MonitorExplanation.AdjustHeight;
  WizardForm.ComponentsList.Height := WizardForm.ComponentsList.Height -
    MonitorExplanation.Height - ScaleY(8);
  MonitorExplanation.Left := WizardForm.ComponentsList.Left;
  MonitorExplanation.Top := WizardForm.ComponentsList.Top +
    WizardForm.ComponentsList.Height + ScaleY(8);
  ThemePage := CreateInputOptionPage(wpSelectComponents, CustomMessage('ThemeTitle'),
    CustomMessage('ThemeSubtitle'),
    CustomMessage('ThemeHelp'), True, False);
  ThemePage.Add(CustomMessage('Graphite'));
  ThemePage.Add(CustomMessage('Midnight'));
  ThemePage.Add(CustomMessage('Forest'));
  ThemePage.Add(CustomMessage('Violet'));
  ThemePage.Add(CustomMessage('Light'));
  ThemePage.SelectedValueIndex := 0;
  ThemePage.CheckListBox.SetBounds(0, ScaleY(50), ScaleX(110), ScaleY(170));
  ThemePage.CheckListBox.OnClickCheck := @UpdateThemePreview;
  ExtractTemporaryFile('graphite.bmp');
  ExtractTemporaryFile('midnight.bmp');
  ExtractTemporaryFile('forest.bmp');
  ExtractTemporaryFile('violet.bmp');
  ExtractTemporaryFile('light.bmp');
  ThemePreview := TBitmapImage.Create(WizardForm);
  ThemePreview.Parent := ThemePage.Surface;
  ThemePreview.SetBounds(ScaleX(120), ScaleY(50), ThemePage.SurfaceWidth - ScaleX(120),
    (ThemePage.SurfaceWidth - ScaleX(120)) * 5 div 8);
  ThemePreview.Stretch := True;
  UpdateThemePreview(nil);
  ProgramLanguagePage := CreateCustomPage(ThemePage.ID,
    CustomMessage('ProgramLanguageTitle'), CustomMessage('ProgramLanguageSubtitle'));
  ProgramLanguageHelp := TNewStaticText.Create(WizardForm);
  ProgramLanguageHelp.Parent := ProgramLanguagePage.Surface;
  ProgramLanguageHelp.WordWrap := True;
  ProgramLanguageHelp.AutoSize := False;
  ProgramLanguageHelp.Width := ProgramLanguagePage.SurfaceWidth;
  ProgramLanguageHelp.Caption := CustomMessage('ProgramLanguageHelp');
  ProgramLanguageHelp.AdjustHeight;
  ProgramLanguageCombo := TNewComboBox.Create(WizardForm);
  ProgramLanguageCombo.Parent := ProgramLanguagePage.Surface;
  ProgramLanguageCombo.Style := csDropDownList;
  ProgramLanguageCombo.SetBounds(0, ProgramLanguageHelp.Height + ScaleY(20),
    ProgramLanguagePage.SurfaceWidth, ScaleY(28));
  ProgramLanguageCodes := TStringList.Create;
  AddProgramLanguages;
  Requested := ExpandConstant('{param:PROGRAMLANG|}');
  Previous := GetPreviousData('ProgramLanguage', '');
  if Requested <> '' then begin
    Index := ProgramLanguageCodes.IndexOf(Lowercase(Requested));
    if Index < 0 then RaiseException(CustomMessage('InvalidLanguage'));
  end else begin
    Index := ProgramLanguageCodes.IndexOf(Previous);
    if Index < 0 then Index := ProgramLanguageCodes.IndexOf(ActiveLanguage);
    if Index < 0 then begin
      Index := ProgramLanguageCodes.IndexOf('en');
      ProgramLanguageHelp.Caption := CustomMessage('ProgramLanguageHelp') + #13#10 +
        CustomMessage('LanguageFallback');
      ProgramLanguageHelp.AdjustHeight;
      ProgramLanguageCombo.Top := ProgramLanguageHelp.Height + ScaleY(20);
    end;
  end;
  ProgramLanguageCombo.ItemIndex := Index;
  ChangeProgramLanguage := TNewCheckBox.Create(WizardForm);
  ChangeProgramLanguage.Parent := ProgramLanguagePage.Surface;
  ChangeProgramLanguage.SetBounds(0, ProgramLanguageCombo.Top + ScaleY(50),
    ProgramLanguagePage.SurfaceWidth, ScaleY(50));
  ChangeProgramLanguage.Caption := CustomMessage('ChangeLanguage');
  ChangeRequested := ExpandConstant('{param:CHANGEPROGRAMLANG|0}');
  if (ChangeRequested <> '0') and (ChangeRequested <> '1') then
    RaiseException(CustomMessage('InvalidChangeLanguage'));
  ChangeProgramLanguage.Checked := ChangeRequested = '1';
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'ProgramLanguage', GetProgramLanguage(''));
  SetPreviousData(PreviousDataKey, 'ClinkChoiceVersion', '1');
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

function GetDefaultsArguments(Param: String): String;
begin
  Result := 'setup-defaults --theme ' + GetInitialTheme('') +
    ' --plugins ' + GetPluginSelection('') + ' --language ' + GetProgramLanguage('');
  if ChangeProgramLanguage.Checked then Result := Result + ' --change-language';
end;

procedure ConfigureInitialPreferences;
var ResultCode: Integer;
begin
  WizardForm.StatusLabel.Caption := CustomMessage('DefaultsStatus');
  if not Exec(ExpandConstant('{app}\LANCTL.exe'), GetDefaultsArguments(''),
    ExpandConstant('{app}'), SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    RaiseException(CustomMessage('DefaultsFailed') + ' (' + IntToStr(ResultCode) + ')');
  if ResultCode <> 0 then
    RaiseException(CustomMessage('DefaultsFailed') + ' (' + IntToStr(ResultCode) + ')');
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
