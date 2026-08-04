#define MyAppName "LANCTL"
#ifndef MyAppVersion
  #define MyAppVersion "0.3.0-beta.2"
#endif
#ifndef BuildRoot
  #define BuildRoot "..\..\dist\LANCTL"
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

[Files]
Source: "{#BuildRoot}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: core

[Icons]
Name: "{group}\LANCTL"; Filename: "{app}\LANCTL.exe"

[Registry]
Root: HKLM; Subkey: "SYSTEM\CurrentControlSet\Control\Session Manager\Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Check: NeedsAddPath('{app}'); Components: path

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
