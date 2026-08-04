[CmdletBinding()] param([string]$Version = '0.3.0-beta.2')
$ErrorActionPreference='Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$') { throw 'Invalid version' }
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $Root
try {
    python -m PyInstaller --clean --noconfirm LANCTL.spec
    Copy-Item packaging\portable\README-portable.txt dist\LANCTL\README-portable.txt
    New-Item -ItemType File -Path dist\LANCTL\LANCTL.portable -Force | Out-Null
    New-Item -ItemType Directory -Force dist\release | Out-Null
    Compress-Archive -Path dist\LANCTL\* -DestinationPath "dist\release\LANCTL-$Version-windows-x64-portable.zip" -Force
    Remove-Item -LiteralPath dist\LANCTL\LANCTL.portable -Force
    $iscc=(Get-Command iscc.exe -ErrorAction SilentlyContinue)
    if (-not $iscc) { throw 'Inno Setup compiler (iscc.exe) is required' }
    & $iscc.Source "/DMyAppVersion=$Version" "/DBuildRoot=$Root\dist\LANCTL" packaging\inno\LANCTL.iss
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }
} finally { Pop-Location }
