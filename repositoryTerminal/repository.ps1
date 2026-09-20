[CmdletBinding()]
param(
    [ValidateSet('install','build','remote','help')]
    [string]$Command = 'install',
    [ValidateSet('stable','beta')][string]$Channel = 'beta',
    [switch]$DryRun
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
try {
    if ($Command -eq 'help') {
        Write-Output @'
LANCTL repository commands (Windows)
  install                      Build local sources and launch the Setup wizard
  install build                Build local sources without installing
  install remote [-Channel beta|stable]   Install a published GitHub release
  install help                 Show this help
  Add -DryRun to inspect the plan without changing anything.
PowerShell: use .\install.cmd instead of install.
Local builds include uncommitted changes. No commit, push or version bump.
Prerequisites: Git, Python with build dependencies, Inno Setup 6.
Save your work, back up your projects and close LANCTL before installation.
'@
        exit 0
    }
    if ($Command -eq 'remote') {
        $OnlineInstaller = Join-Path $Root 'install.ps1'
        if ($DryRun) {
            Write-Output "REMOTE: $OnlineInstaller -Channel $Channel -Version auto"
            exit 0
        }
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $OnlineInstaller -Channel $Channel -Version auto
        exit $LASTEXITCODE
    }
    # Read metadata without importing the application or migrating user data.
    $Metadata = Get-Content -LiteralPath (Join-Path $Root 'src\lanctl\__init__.py') -Raw
    $Match = [regex]::Match($Metadata, '(?m)^__version__\s*=\s*"(\d+\.\d+\.\d+(?:-(?:alpha|beta|rc)\.\d+)?)"\s*$')
    if (-not $Match.Success) { throw 'Cannot determine repository version' }
    $Version = $Match.Groups[1].Value
    $Builder = Join-Path $Root 'scripts\build-windows.ps1'
    $Setup = Join-Path $Root "dist\release\LANCTL-$Version-windows-x64-setup.exe"
    Write-Output "BUILD: $Builder -Version $Version -AllowDirty"
    if ($Command -eq 'install') { Write-Output "INSTALL: $Setup (interactive wizard, UAC)" }
    if ($DryRun) { exit 0 }
    Write-Output 'Building local changes. Existing build artifacts may be replaced; user projects are not removed.'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Builder -Version $Version -AllowDirty
    if ($LASTEXITCODE -ne 0) { throw "Build failed (exit $LASTEXITCODE); installation was NOT started" }
    if ($Command -eq 'build') { exit 0 }
    if (-not (Test-Path -LiteralPath $Setup -PathType Leaf)) { throw "Setup was not generated: $Setup" }
    # Keep the wizard visible: the user chooses destination and confirms elevation.
    $Installer = Start-Process -FilePath $Setup -Verb RunAs -Wait -PassThru
    if ($Installer.ExitCode -ne 0) { throw "Setup did not complete successfully (exit $($Installer.ExitCode))" }
    Write-Output 'Installation completed. Open a new terminal and check lanip --version.'
    exit 0
} catch {
    [Console]::Error.WriteLine("[REPOSITORY.ERROR] {0}" -f $_.Exception.Message)
    exit 1
}
