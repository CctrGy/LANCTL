param([switch]$RemoveClink)
$ErrorActionPreference = 'Stop'
$LauncherPath = Join-Path $PSScriptRoot 'LANCTL.exe'
if (-not (Test-Path -LiteralPath $LauncherPath -PathType Leaf)) { throw 'LANCTL.exe is missing from this portable directory.' }
$ClinkAction = if ($RemoveClink) { 'uninstall' } else { 'install' }
& $LauncherPath completions $ClinkAction
if ($LASTEXITCODE -ne 0) { throw 'Clink integration failed. See LANCTL diagnostics.' }
