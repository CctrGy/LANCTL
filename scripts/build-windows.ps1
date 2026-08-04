[CmdletBinding()] param([string]$Version = '0.3.0-beta.4')
$ErrorActionPreference='Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$') { throw 'Invalid version' }
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $Root
try {
    python -m PyInstaller --clean --noconfirm LANCTL.spec
    New-Item -ItemType Directory -Force dist\release | Out-Null
    $portable=Join-Path $Root 'dist\portable-staging'
    if(Test-Path -LiteralPath $portable){Remove-Item -LiteralPath $portable -Recurse -Force}
    New-Item -ItemType Directory -Path $portable | Out-Null
    Copy-Item dist\LANCTL.exe (Join-Path $portable 'LANCTL.exe')
    Copy-Item dist\LANCTL-GUI.exe (Join-Path $portable 'LANCTL-GUI.exe')
    Copy-Item packaging\portable\README-portable.txt (Join-Path $portable 'README-portable.txt')
    Set-Content -LiteralPath (Join-Path $portable 'LANCTL.portable') -Value 'LANCTL-PORTABLE-V1' -Encoding ascii
    Compress-Archive -Path "$portable\*" -DestinationPath "dist\release\LANCTL-$Version-windows-x64-portable.zip" -Force
    $iscc=(Get-Command iscc.exe -ErrorAction SilentlyContinue)
    if (-not $iscc) { throw 'Inno Setup compiler (iscc.exe) is required' }
    & $iscc.Source "/DMyAppVersion=$Version" "/DBuildRoot=$Root\dist" packaging\inno\LANCTL.iss
    if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }
} finally { Pop-Location }
