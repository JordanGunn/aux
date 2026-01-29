# AUx Skills - Unified Installation
# Installs the aux CLI and validates system dependencies
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CliDir = Join-Path $ScriptDir "cli"

Write-Output "AUx Skills Installation"
Write-Output "======================="
Write-Output ""

# -----------------------------------------------------------------------------
# Phase 1: Check system dependencies
# -----------------------------------------------------------------------------
Write-Output "Checking system dependencies..."

$errors = 0

# Check for uv (required for installation)
if (Get-Command uv -ErrorAction SilentlyContinue) {
    $uvVersion = & uv --version 2>$null | Select-Object -First 1
    Write-Output "  + uv: $uvVersion"
} else {
    Write-Output "  x uv not found"
    Write-Output "    Install from: https://docs.astral.sh/uv/"
    $errors++
}

# Check for ripgrep (required for grep skill)
if (Get-Command rg -ErrorAction SilentlyContinue) {
    $rgVersion = & rg --version 2>$null | Select-Object -First 1
    Write-Output "  + rg: $rgVersion"
} else {
    Write-Output "  x rg (ripgrep) not found"
    Write-Output "    Install: scoop install ripgrep | choco install ripgrep"
    $errors++
}

# Check for fd (required for find skill)
$hasFd = Get-Command fd -ErrorAction SilentlyContinue
$hasFdfind = Get-Command fdfind -ErrorAction SilentlyContinue
if ($hasFd) {
    $fdVersion = & fd --version 2>$null | Select-Object -First 1
    Write-Output "  + fd: $fdVersion"
} elseif ($hasFdfind) {
    $fdVersion = & fdfind --version 2>$null | Select-Object -First 1
    Write-Output "  + fdfind: $fdVersion"
} else {
    Write-Output "  x fd/fdfind not found"
    Write-Output "    Install: scoop install fd | choco install fd"
    $errors++
}

# Check for git (required for diff skill)
if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitVersion = & git --version 2>$null
    Write-Output "  + git: $gitVersion"
} else {
    Write-Output "  x git not found"
    $errors++
}

# Check for diff (required for diff skill)
if (Get-Command diff -ErrorAction SilentlyContinue) {
    $diffVersion = & diff --version 2>$null | Select-Object -First 1
    Write-Output "  + diff: $diffVersion"
} else {
    Write-Output "  x diff not found"
    Write-Output "    Note: diff is typically available via Git for Windows"
    $errors++
}

Write-Output ""

if ($errors -gt 0) {
    Write-Error "ERROR: $errors missing system dependencies"
    Write-Output "Please install the missing dependencies and re-run this script."
    exit 1
}

Write-Output "All system dependencies available."
Write-Output ""

# -----------------------------------------------------------------------------
# Phase 2: Install aux CLI
# -----------------------------------------------------------------------------
Write-Output "Installing aux CLI..."

$pyproject = Join-Path $CliDir "pyproject.toml"
if (-not (Test-Path $pyproject)) {
    Write-Error "ERROR: CLI not found at $CliDir"
    Write-Output "Ensure you're running this from the aux repository root."
    exit 1
}

# Install as a tool using uv (creates isolated environment)
Push-Location $CliDir
try {
    & uv tool install --editable . --force --quiet
} finally {
    Pop-Location
}

Write-Output "  + aux CLI installed (via uv tool)"
Write-Output ""

# -----------------------------------------------------------------------------
# Phase 3: Verify installation
# -----------------------------------------------------------------------------
Write-Output "Verifying installation..."

if (-not (Get-Command aux -ErrorAction SilentlyContinue)) {
    Write-Error "  x aux command not found in PATH"
    Write-Output "    You may need to activate your virtual environment or add Scripts to PATH"
    exit 1
}

$auxVersion = & aux --version 2>$null
Write-Output "  + aux: $auxVersion"

# Run doctor to verify all dependencies
Write-Output ""
Write-Output "Running aux doctor..."
& aux doctor

Write-Output ""
Write-Output "======================="
Write-Output "Installation complete!"
Write-Output ""
Write-Output "Available skills:"
Write-Output "  - grep: Agent-assisted text search"
Write-Output "  - find: Agent-assisted file enumeration"
Write-Output "  - diff: Deterministic file comparison"
Write-Output "  - ls:   Deterministic directory inspection"
Write-Output ""
Write-Output "Usage:"
Write-Output '  aux grep "pattern" --root /path --glob "**/*.py"'
Write-Output '  aux find --root /path --glob "**/*.go" --type file'
Write-Output '  aux diff /path/a /path/b'
Write-Output '  aux ls /path --depth 2 --sort size'
Write-Output ""
Write-Output "For skill invocation via scripts:"
Write-Output '  ./skills/grep/scripts/skill.ps1 run "pattern" --root /path'
