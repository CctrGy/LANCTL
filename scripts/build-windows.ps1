[CmdletBinding()] param(
    [string]$Version = '0.3.0-beta.21',
    [switch]$SkipInstaller,
    [switch]$AllowDirty,
    [string]$SigningCertificateThumbprint = '',
    [string]$TimestampUrl = 'http://timestamp.digicert.com',
    [switch]$RequireSignature
)
$ErrorActionPreference='Stop'
if ($Version -notmatch '^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$') { throw 'Invalid version' }
$Root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $Root
try {
    if ($RequireSignature -and -not $SigningCertificateThumbprint) {
        throw 'Authenticode signing is required but no certificate thumbprint was provided'
    }
    function Get-SignTool {
        $command = Get-Command signtool.exe -ErrorAction SilentlyContinue
        if ($command) { return $command.Source }
        $kits = "${env:ProgramFiles(x86)}\Windows Kits\10\bin"
        if (Test-Path -LiteralPath $kits) {
            return Get-ChildItem -LiteralPath $kits -Filter signtool.exe -Recurse -File |
                Where-Object { $_.FullName -match '\\x64\\signtool\.exe$' } |
                Sort-Object FullName -Descending |
                Select-Object -First 1 -ExpandProperty FullName
        }
        return $null
    }
    function Sign-And-Verify([string]$Path) {
        if (-not $SigningCertificateThumbprint) {
            if ($RequireSignature) { throw "Authenticode signing is required: $Path" }
            return
        }
        $signTool = Get-SignTool
        if (-not $signTool) { throw 'signtool.exe is required for Authenticode signing' }
        & $signTool sign /sha1 $SigningCertificateThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $Path
        if ($LASTEXITCODE -ne 0) { throw "Authenticode signing failed: $Path" }
        $signature = Get-AuthenticodeSignature -LiteralPath $Path
        if ($signature.Status -ne 'Valid') {
            throw "Authenticode verification failed ($($signature.Status)): $Path"
        }
    }
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
    & $Python scripts/verify-version.py $Version
    if ($LASTEXITCODE -ne 0) { throw 'Build version does not match the application version' }
    $VersionInfo = Join-Path $Root 'build\windows-version-info.generated.txt'
    & $Python scripts/generate-windows-version-info.py $Version $Revision $VersionInfo
    if ($LASTEXITCODE -ne 0) { throw 'Windows version metadata generation failed' }
    $env:LANCTL_VERSION_INFO = $VersionInfo
    & $Python -m PyInstaller --clean --noconfirm LANCTL.spec
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed' }
    if (-not (Test-Path -LiteralPath 'dist\lanip.exe')) {
        throw 'The unified PyInstaller build did not produce dist\lanip.exe'
    }
    if (-not (Test-Path -LiteralPath 'dist\lanwire.exe')) {
        throw 'The unified PyInstaller build did not produce dist\lanwire.exe'
    }
    if (-not (Test-Path -LiteralPath 'dist\lanmon.exe')) {
        throw 'The unified PyInstaller build did not produce dist\lanmon.exe'
    }
    if (-not (Test-Path -LiteralPath 'dist\lanrack.exe')) { throw 'PyInstaller did not produce dist\lanrack.exe' }
    if (-not (Test-Path -LiteralPath 'dist\lanaccess.exe')) { throw 'PyInstaller did not produce dist\lanaccess.exe' }
    foreach ($binary in @('dist\LANCTL.exe','dist\lanip.exe','dist\lanwire.exe','dist\lanmon.exe','dist\lanrack.exe','dist\lanaccess.exe')) {
        Sign-And-Verify (Resolve-Path -LiteralPath $binary).Path
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
    Copy-Item dist\lanip.exe (Join-Path $portable 'lanip.exe')
    Copy-Item dist\lanwire.exe (Join-Path $portable 'lanwire.exe')
    Copy-Item dist\lanmon.exe (Join-Path $portable 'lanmon.exe')
    Copy-Item dist\lanrack.exe (Join-Path $portable 'lanrack.exe')
    Copy-Item dist\lanaccess.exe (Join-Path $portable 'lanaccess.exe')
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
        Sign-And-Verify (Resolve-Path -LiteralPath "dist\release\LANCTL-$Version-windows-x64-setup.exe").Path
    }
    & $Python scripts/release-metadata.py $Version $Revision dist/release
    if ($LASTEXITCODE -ne 0) { throw 'Release metadata failed' }
    & $Python scripts/generate-hashes.py dist/release
    if ($LASTEXITCODE -ne 0) { throw 'Checksum generation failed' }
    & $Python scripts/verify-release.py dist/release
    if ($LASTEXITCODE -ne 0) { throw 'Release verification failed' }
} finally {
    Remove-Item Env:\LANCTL_VERSION_INFO -ErrorAction SilentlyContinue
    Pop-Location
}
