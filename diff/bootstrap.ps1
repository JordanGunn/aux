$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir "scripts/src"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "error: uv not found. Install from https://docs.astral.sh/uv/"
    exit 1
}

$pyproject = Join-Path $SrcDir "pyproject.toml"
if (-not (Test-Path $pyproject)) {
    Write-Error "error: missing $pyproject"
    exit 1
}

Push-Location $SrcDir
try {
    & uv sync
} finally {
    Pop-Location
}

Write-Output "ok: diff bootstrap complete"
