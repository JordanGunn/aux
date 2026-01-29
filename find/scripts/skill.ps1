#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir "src"

function Show-Help {
    @"
find - Agent-assisted file enumeration (deterministic fd wrapper)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  run [opts]                   Execute a deterministic file enumeration

Options (run):
  --root <path>                Root directory (default: .)
  --pattern <pattern>          Glob pattern for names (repeatable)
  --extension <ext>            File extension without dot (repeatable)
  --exclude <pattern>          Exclude pattern (repeatable)
  --type <file|directory|any>  Entry type (default: file)
  --max-depth <n>              Maximum directory depth
  --max-results <n>            Max results (default: 1000)
  --format <auto|human|jsonl>  Output format (default: auto)
  --hidden                     Include hidden files
  --follow                     Follow symlinks
  --no-ignore                  Ignore .gitignore rules
  --stdin                      Read plan JSON from stdin
"@
}

function Test-Validate {
    $errors = 0

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Error "error: uv not found. Install from https://docs.astral.sh/uv/"
        $errors++
    }

    $hasFd = [bool](Get-Command fd -ErrorAction SilentlyContinue)
    $hasFdFind = [bool](Get-Command fdfind -ErrorAction SilentlyContinue)
    if (-not $hasFd -and -not $hasFdFind) {
        Write-Error "error: fd not found. Install fd-find (binary may be 'fdfind' on Debian/Ubuntu)."
        $errors++
    }

    $pyproject = Join-Path $SrcDir "pyproject.toml"
    if (-not (Test-Path $pyproject)) {
        Write-Error "error: missing $pyproject"
        $errors++
    }

    $cli = Join-Path $SrcDir "cli.py"
    if (-not (Test-Path $cli)) {
        Write-Error "error: missing $cli"
        $errors++
    }

    if ($errors -gt 0) {
        exit 1
    }

    Write-Output "ok: find skill is runnable"
}

function Invoke-Run {
    param([string[]]$Arguments)
    $cli = Join-Path $SrcDir "cli.py"
    & uv run -q --no-progress --project $SrcDir python $cli run @Arguments
}

$command = if ($args.Count -gt 0) { $args[0] } else { "help" }

switch ($command) {
    "help" { Show-Help }
    "validate" { Test-Validate }
    "run" { Invoke-Run -Arguments ($args | Select-Object -Skip 1) }
    default {
        Write-Error "error: unknown command '$command'"
        Write-Error "run 'find help' for usage"
        exit 1
    }
}
