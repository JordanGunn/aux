#!/usr/bin/env pwsh
# usages skill - Symbol cross-reference (definitions + references)
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
usages - Symbol cross-reference: definitions + references in one call

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts] <symbol>          Execute a symbol cross-reference search

Usage (run):
  skill.ps1 run <symbol> --root <path> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  <symbol>                     Exact symbol name (literal string, not regex)
  --root <path>                Root directory (required)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --language <name>            Tree-sitter language override
  --no-definitions             Skip AST definition tagging
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --max-results <n>            Max total results to return

Examples:
  skill.ps1 run DataProcessor --root ./src --glob "**/*.py"
  '{"root":"/path","symbol":"DataProcessor","globs":["**/*.py"]}' | skill.ps1 run --stdin

Execution backend: aux usages (aux-skills CLI)
"@
}

function Test-Validate {
    if (-not (Get-Command aux -ErrorAction SilentlyContinue)) {
        Write-Error "error: aux CLI not found. Install with: pip install aux-skills"
        exit 1
    }

    # Check optional tree-sitter dependency
    $tsCheck = python -c "import tree_sitter" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "warn: tree-sitter not installed (definition tagging unavailable). Install with: pip install 'aux-skills[query]'"
    }

    # Delegate to CLI doctor for full dependency check
    & aux doctor
}

function Get-Schema {
    & aux usages --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux usages --plan $plan
    } else {
        # CLI argument passthrough
        & aux usages @Arguments
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
