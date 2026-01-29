# ls skill bootstrap - verifies aux CLI is available
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check for aux CLI
if (-not (Get-Command aux -ErrorAction SilentlyContinue)) {
    Write-Error "error: aux CLI not found"
    Write-Output "Install with: pip install aux-skills"
    Write-Output "Or from source: pip install -e /path/to/aux/cli"
    exit 1
}

# Validate dependencies via CLI doctor
try {
    $null = & aux doctor 2>&1
} catch {
    Write-Error "error: aux doctor check failed"
    & aux doctor
    exit 1
}

Write-Output "ok: ls skill ready (aux CLI available)"
