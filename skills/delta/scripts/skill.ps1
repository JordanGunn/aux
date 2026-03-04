#!/usr/bin/env pwsh
# delta skill - Semantic git diff (symbols added/removed since a ref)
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
delta - Semantic git diff: files changed + symbols added/removed since a ref

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a semantic git diff

Usage (run):
  skill.ps1 run --root <path> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Git repo root or subdirectory (required)
  --ref-from <ref>             Base ref (default: HEAD)
  --ref-to <ref>               Target ref (default: working tree)
  --glob <pattern>             Filter changed files by glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --language <name>            Tree-sitter language override
  --stat-only                  Skip symbol analysis, return only line counts
  --max-files <n>              Max files to analyze

Examples:
  skill.ps1 run --root .
  skill.ps1 run --root . --ref-from HEAD~3 --glob "**/*.py"
  '{"root":".","ref_from":"HEAD~2","globs":["**/*.py"]}' | skill.ps1 run --stdin

Execution backend: aux delta (aux-skills CLI)
"@
}

function Test-Validate {
    if (-not (Get-Command aux -ErrorAction SilentlyContinue)) {
        Write-Error "error: aux CLI not found. Install with: pip install aux-skills"
        exit 1
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "error: git not found (required for delta). Install git and ensure it is in PATH."
        exit 1
    }

    # Check optional tree-sitter dependency
    $tsCheck = python -c "import tree_sitter" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "warn: tree-sitter not installed (semantic symbol diff unavailable; stat-only mode will run). Install with: pip install 'aux-skills[query]'"
    }

    # Delegate to CLI doctor for full dependency check
    & aux doctor
}

function Get-Schema {
    & aux delta --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux delta --plan $plan
    } else {
        # CLI argument passthrough
        & aux delta @Arguments
    }
}

$command = if ($args.Count -gt 0) { $args[0] } else { "help" }

switch ($command) {
    "help" { Show-Help }
    "validate" { Test-Validate }
    "schema" { Get-Schema }
    "run" { Invoke-Run -Arguments ($args | Select-Object -Skip 1) }
    default {
        Write-Error "error: unknown command '$command'"
        Write-Error "run 'skill.ps1 help' for usage"
        exit 1
    }
}
