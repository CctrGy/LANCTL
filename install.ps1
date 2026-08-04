[CmdletBinding()]
param(
    [ValidateSet('stable','beta')][string]$Channel = 'stable',
    [ValidatePattern('^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$')][string]$Version,
    [ValidateSet('standard','monitor')][string]$Mode = 'standard',
    [switch]$Portable,
    [switch]$ConfigureAccess,
    [switch]$Yes,
    [switch]$Uninstall,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'
$Repository = 'CctrGy/LANCTL'

function Show-Usage {
    @'
LANCTL online installer
  .\install.ps1 [-Channel stable|beta] [-Version VERSION]
                [-Mode standard|monitor] [-Portable] [-ConfigureAccess] [-Yes]
  .\install.ps1 -Uninstall [-Yes]

-ConfigureAccess only starts LANCTL's local interactive wizard after installation.
It never enables SSH or HTTPS non-interactively.
'@
}
function Get-Release {
    $headers = @{ 'Accept'='application/vnd.github+json'; 'X-GitHub-Api-Version'='2022-11-28' }
    if ($Version) {
        return Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$Repository/releases/tags/v$Version"
    }
    $releases = Invoke-RestMethod -Headers $headers -Uri "https://api.github.com/repos/$Repository/releases?per_page=50"
    $selected = $releases | Where-Object {
        -not $_.draft -and (($Channel -eq 'beta' -and $_.prerelease) -or ($Channel -eq 'stable' -and -not $_.prerelease))
    } | Select-Object -First 1
    if (-not $selected) { throw "No release found for channel $Channel" }
    return $selected
}
function Get-Asset($Release,[string]$Name) {
    $asset = $Release.assets | Where-Object { $_.name -ceq $Name } | Select-Object -First 1
    if (-not $asset) { throw "Required release asset is missing: $Name" }
    if ($asset.browser_download_url -notmatch '^https://github\.com/CctrGy/LANCTL/releases/download/') { throw 'Unexpected asset origin' }
    return $asset
}
function Download-Asset($Asset,[string]$Destination) {
    Invoke-WebRequest -UseBasicParsing -Uri $Asset.browser_download_url -OutFile $Destination
}
function Assert-Hash([string]$File,[string]$SumsFile,[string]$Name) {
    $escaped = [regex]::Escape($Name)
    $line = Get-Content -LiteralPath $SumsFile | Where-Object { $_ -match "^([a-fA-F0-9]{64})  $escaped$" } | Select-Object -First 1
    if (-not $line) { throw "No SHA-256 entry for $Name" }
    $expected = ([regex]::Match($line,'^[a-fA-F0-9]{64}')).Value.ToLowerInvariant()
    $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $File).Hash.ToLowerInvariant()
    if ($actual -ne $expected) { throw "SHA-256 verification failed for $Name" }
}
function Expand-SafeZip([string]$Archive,[string]$Destination) {
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $root = [IO.Path]::GetFullPath($Destination + [IO.Path]::DirectorySeparatorChar)
    $zip = [IO.Compression.ZipFile]::OpenRead($Archive)
    try {
        foreach ($entry in $zip.Entries) {
            $target = [IO.Path]::GetFullPath((Join-Path $Destination $entry.FullName))
            if (-not $target.StartsWith($root,[StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe ZIP entry detected' }
        }
    } finally { $zip.Dispose() }
    Expand-Archive -LiteralPath $Archive -DestinationPath $Destination -Force
}

if ($Help) { Show-Usage; exit 0 }
if ($Uninstall) {
    $uninstaller = Join-Path $env:ProgramFiles 'LANCTL\unins000.exe'
    if (-not (Test-Path -LiteralPath $uninstaller)) { throw 'LANCTL standard installation was not found' }
    if (-not $Yes) { $answer=Read-Host 'Uninstall LANCTL but preserve projects/configuration? [y/N]'; if ($answer -notmatch '^(y|yes|s|si)$') { exit 1 } }
    Start-Process -FilePath $uninstaller -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait
    exit 0
}

$release = Get-Release
$resolvedVersion = $release.tag_name -replace '^v',''
if ($resolvedVersion -notmatch '^\d+\.\d+\.\d+(-(alpha|beta|rc)\.\d+)?$') { throw 'Release tag has an unsafe version format' }
$artifactName = if ($Portable) { "LANCTL-$resolvedVersion-windows-x64-portable.zip" } else { "LANCTL-$resolvedVersion-windows-x64-setup.exe" }
$temporary = Join-Path ([IO.Path]::GetTempPath()) ("lanctl-install-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temporary | Out-Null
try {
    $artifact = Get-Asset $release $artifactName
    $sums = Get-Asset $release 'SHA256SUMS.txt'
    $artifactPath = Join-Path $temporary $artifactName
    $sumsPath = Join-Path $temporary 'SHA256SUMS.txt'
    Download-Asset $artifact $artifactPath; Download-Asset $sums $sumsPath
    Assert-Hash $artifactPath $sumsPath $artifactName
    if ($Portable) {
        $portableBase=Join-Path $env:LOCALAPPDATA 'Programs\LANCTL';$destination = Join-Path $portableBase $resolvedVersion
        $staging = "$destination.new-$([guid]::NewGuid().ToString('N'))"
        New-Item -ItemType Directory -Path $staging -Force | Out-Null
        Expand-SafeZip $artifactPath $staging
        $previousData=$null
        if(Test-Path -LiteralPath (Join-Path $destination 'data\lanctl')){$previousData=Join-Path $destination 'data\lanctl'}
        elseif(Test-Path -LiteralPath $portableBase){$previous=Get-ChildItem -LiteralPath $portableBase -Directory | Where-Object {$_.Name -notmatch '\.(new|previous)-'} | Sort-Object LastWriteTime -Descending | Select-Object -First 1;if($previous -and (Test-Path -LiteralPath (Join-Path $previous.FullName 'data\lanctl'))){$previousData=Join-Path $previous.FullName 'data\lanctl'}}
        if($previousData){New-Item -ItemType Directory -Path (Join-Path $staging 'data') -Force|Out-Null;Copy-Item -LiteralPath $previousData -Destination (Join-Path $staging 'data\lanctl') -Recurse}
        if (Test-Path -LiteralPath $destination) {
            $backup = "$destination.previous-$([guid]::NewGuid().ToString('N'))"
            Move-Item -LiteralPath $destination -Destination $backup
            Write-Host "Previous portable installation preserved at $backup"
        }
        Move-Item -LiteralPath $staging -Destination $destination
        if ((Get-Content -LiteralPath (Join-Path $destination 'LANCTL.portable') -Raw).Trim() -ne 'LANCTL-PORTABLE-V1') { throw 'Portable marker is missing or invalid' }
        if (Test-Path -LiteralPath (Join-Path $destination '_internal')) { throw 'Portable package unexpectedly contains _internal' }
        Write-Host "Portable LANCTL installed at $destination (PATH is not modified)."
    } else {
        $arguments = @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/MODE=$Mode")
        if ($Yes) { $arguments += '/SP-' }
        $process = Start-Process -FilePath $artifactPath -ArgumentList $arguments -Wait -PassThru
        if ($process.ExitCode -ne 0) { throw "Setup failed with exit code $($process.ExitCode)" }
        $installRoot=Join-Path $env:ProgramFiles 'LANCTL';$dataRoot=Join-Path $env:ProgramData 'LANCTL'
        if (-not (Test-Path -LiteralPath (Join-Path $installRoot 'LANCTL.exe'))) { throw 'Setup did not install LANCTL.exe' }
        foreach($unexpected in @('LANCTL.portable','_internal','data')) { if(Test-Path -LiteralPath (Join-Path $installRoot $unexpected)){throw "Unsafe installed layout: $unexpected"} }
        if (-not (Test-Path -LiteralPath $dataRoot)) { throw 'Setup did not create the ProgramData root' }
        $systemPath=[Environment]::GetEnvironmentVariable('Path','Machine')
        if ($systemPath -notlike "*$installRoot*") { throw 'Setup did not add LANCTL to the system PATH' }
        $configuredData=[Environment]::GetEnvironmentVariable('LANCTL_DATA_DIR','Machine')
        if ($configuredData -and ([IO.Path]::GetFullPath($configuredData) -ne [IO.Path]::GetFullPath($dataRoot))) { throw 'Existing LANCTL_DATA_DIR points outside the installed data root' }
    }
    if ($ConfigureAccess) {
        if ($Yes) { Write-Warning 'Remote access cannot be enabled with -Yes; run lanctl access setup-wizard interactively.' }
        else { & lanctl access setup-wizard }
    }
} finally {
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Recurse -Force }
}
