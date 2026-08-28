[CmdletBinding()] param(
    [string]$Version = '0.3.0-beta.20',
    [switch]$SkipInstaller,
    [switch]$AllowDirty
)
$ErrorActionPreference='Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$') { throw 'Invalid version' }
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $Root
try {
    if (-not $AllowDirty) {
        $Dirty = & git status --porcelain
        if ($LASTEXITCODE -ne 0) { throw 'Git status failed' }
        if ($Dirty) { throw 'Release builds require a clean Git working tree' }
    }
    $Revision = (& git rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $Revision -notmatch '^[0-9a-f]{40}$') { throw 'Invalid Git revision' }
    # Usa el entorno reproducible del repositorio cuando existe.
    $Python = Join-Path $Root '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $Python)) { $Python = 'python' }
    & $Python -m PyInstaller --clean --noconfirm LANCTL.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
    if (-not (Test-Path -LiteralPath 'dist\lanip.exe')) {
        throw 'The unified PyInstaller build did not produce dist\lanip.exe'
    }
    if (-not (Test-Path -LiteralPath 'dist\lanwire.exe')) {
        throw 'The unified PyInstaller build did not produce dist\lanwire.exe'
    }
    $release = Join-Path $Root 'dist\release'
    if (Test-Path -LiteralPath $release) {
        Remove-Item -LiteralPath $release -Recurse -Force
    }
    New-Item -ItemType Directory -Path $release | Out-Null
    $portable=Join-Path $Root 'dist\portable-staging'
    if(Test-Path -LiteralPath $portable){Remove-Item -LiteralPath $portable -Recurse -Force}
    New-Item -ItemType Directory -Path $portable | Out-Null
    Copy-Item dist\LANCTL.exe (Join-Path $portable 'LANCTL.exe')
    Copy-Item dist\LANCTL-GUI.exe (Join-Path $portable 'LANCTL-GUI.exe')
    Copy-Item dist\lanip.exe (Join-Path $portable 'lanip.exe')
    Copy-Item dist\lanwire.exe (Join-Path $portable 'lanwire.exe')
    Copy-Item packaging\portable\README-portable.txt (Join-Path $portable 'README-portable.txt')
    Set-Content -LiteralPath (Join-Path $portable 'LANCTL.portable') -Value 'LANCTL-PORTABLE-V1' -Encoding ascii
    Compress-Archive -Path "$portable\*" -DestinationPath "dist\release\LANCTL-$Version-windows-x64-portable.zip" -Force
    if (-not $SkipInstaller) {
        $iscc=(Get-Command iscc.exe -ErrorAction SilentlyContinue).Source
        if (-not $iscc) {
            $iscc = @(
                "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
                "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
                "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
            ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
        }
        if (-not $iscc) { throw 'Inno Setup compiler (iscc.exe) is required' }
        & $iscc "/DMyAppVersion=$Version" "/DBuildRoot=$Root\dist" packaging\inno\LANCTL.iss
        if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed' }
    }
    & $Python scripts/release-metadata.py $Version $Revision dist/release
    if ($LASTEXITCODE -ne 0) { throw 'Release metadata failed' }
    & $Python scripts/generate-hashes.py dist/release
    if ($LASTEXITCODE -ne 0) { throw 'Checksum generation failed' }
    & $Python scripts/verify-release.py dist/release
    if ($LASTEXITCODE -ne 0) { throw 'Release verification failed' }
} finally { Pop-Location }
