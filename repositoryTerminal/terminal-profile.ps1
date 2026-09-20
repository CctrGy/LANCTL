[CmdletBinding()]
param(
    [string]$Executable = '',
    [switch]$DryRun,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'
try {
    if ($Help) {
        Write-Output 'terminal-profile.cmd [-Executable PATH\LANCTL.exe] [-DryRun]'
        Write-Output 'Creates a per-user LANCTL profile running --cli; existing LANCTL profiles are preserved.'
        exit 0
    }
    if (-not $env:LOCALAPPDATA) { throw 'LOCALAPPDATA is unavailable' }
    # Never rewrite settings.json: preserve comments, personal profiles and defaults.
    $SettingsPaths = @(
        (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\settings.json'),
        (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal Preview\settings.json')
    )
    $Packages = Join-Path $env:LOCALAPPDATA 'Packages'
    if (Test-Path -LiteralPath $Packages) {
        $SettingsPaths += @(Get-ChildItem -LiteralPath $Packages -Directory -Filter 'Microsoft.WindowsTerminal*' |
            ForEach-Object { Join-Path $_.FullName 'LocalState\settings.json' })
    }
    $Fragment = Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\Fragments\LANCTL\lanctl-cli.json'
    foreach ($SettingsPath in $SettingsPaths) {
        if (Test-Path -LiteralPath $SettingsPath) {
            $Raw = Get-Content -LiteralPath $SettingsPath -Raw
            # Conservative JSONC-compatible detection: a matching name, including
            # a commented profile, prevents creating an accidental duplicate.
            if ($Raw -match '"name"\s*:\s*"LANCTL"') {
                Write-Output "LANCTL already exists in $SettingsPath. No changes made."
                exit 0
            }
        }
    }
    $FragmentRoots = @((Join-Path $env:LOCALAPPDATA 'Microsoft\Windows Terminal\Fragments'))
    if ($env:ProgramData) { $FragmentRoots += (Join-Path $env:ProgramData 'Microsoft\Windows Terminal\Fragments') }
    foreach ($FragmentRoot in $FragmentRoots) {
        if (Test-Path -LiteralPath $FragmentRoot) {
            foreach ($Other in Get-ChildItem -LiteralPath $FragmentRoot -Recurse -File -Filter '*.json') {
                if ((Get-Content -LiteralPath $Other.FullName -Raw) -match '"name"\s*:\s*"LANCTL"') {
                    Write-Output "LANCTL already exists in $($Other.FullName). No changes made."
                    exit 0
                }
            }
        }
    }
    if (-not $Executable) {
        $Installed = Join-Path $env:ProgramFiles 'LANCTL\LANCTL.exe'
        if (Test-Path -LiteralPath $Installed -PathType Leaf) { $Executable = $Installed }
        else {
            $Resolved = Get-Command lanctl.exe -CommandType Application -ErrorAction SilentlyContinue
            if ($Resolved) { $Executable = $Resolved.Source }
        }
    }
    if (-not $Executable -or -not (Test-Path -LiteralPath $Executable -PathType Leaf)) {
        throw 'LANCTL executable not found. Install LANCTL or specify -Executable.'
    }
    $Executable = (Resolve-Path -LiteralPath $Executable).Path
    if ($Executable.Contains('"') -or [IO.Path]::GetExtension($Executable) -ine '.exe') {
        throw 'Expected an executable .exe path'
    }
    $Profile = [ordered]@{
        guid = '{4dc1c36c-45b6-4a1e-94c4-324c37683786}'
        name = 'LANCTL'
        commandline = ('"{0}" --cli' -f $Executable)
        startingDirectory = '%USERPROFILE%'
        icon = $Executable
        hidden = $false
    }
    $Json = @{ profiles = @($Profile) } | ConvertTo-Json -Depth 5
    Write-Output "Profile destination: $Fragment"
    if ($DryRun) { Write-Output $Json; exit 0 }
    $Directory = Split-Path -Parent $Fragment
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    # Do not overwrite an existing unrelated file at our destination.
    $Bytes = [Text.UTF8Encoding]::new($false).GetBytes($Json)
    $Stream = [IO.File]::Open($Fragment, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try { $Stream.Write($Bytes, 0, $Bytes.Length) } finally { $Stream.Dispose() }
    Write-Output 'LANCTL profile created. Restart Windows Terminal to load it. Default profile unchanged.'
    exit 0
} catch {
    [Console]::Error.WriteLine('[REPOSITORY.TERMINAL.ERROR] {0}' -f $_.Exception.Message)
    exit 1
}
