# Compile the wizard only. Fixtures are inert bytes, never installed or published.
[CmdletBinding()] param([string]$Compiler = '')
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if (-not $Compiler) {
    $command = Get-Command iscc.exe -ErrorAction SilentlyContinue
    if ($command) { $Compiler = $command.Source }
    else {
        $Compiler = @(
            "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
            "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
        ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }
}
if (-not $Compiler) { throw 'Inno Setup 6 is required for the wizard compile check' }
$Fixture = Join-Path ([System.IO.Path]::GetTempPath()) ('lanctl-inno-check-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $Fixture | Out-Null
try {
    foreach ($name in @('LANCTL','lanctl-window','lanip','lanwire','lanrack','lanaccess','lanmon')) {
        [System.IO.File]::WriteAllBytes((Join-Path $Fixture "$name.exe"), [byte[]]@(0x4D,0x5A))
    }
    $Output = Join-Path $Fixture 'compiled-wizard-only'
    New-Item -ItemType Directory -Path $Output | Out-Null
    & $Compiler /Qp "/DBuildRoot=$Fixture" "/O$Output" (Join-Path $Root 'packaging\inno\LANCTL.iss')
    if ($LASTEXITCODE -ne 0) { throw 'Inno wizard compilation failed' }
} finally {
    Remove-Item -LiteralPath $Fixture -Recurse -Force
}
