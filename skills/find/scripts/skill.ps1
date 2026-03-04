#!/usr/bin/env pwsh
# find skill - Read-only tree-sitter structural search
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
find - Read-only tree-sitter structural search (AST-aware)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts] <query>           Execute a structural search

Usage (run):
  skill.ps1 run <query> --root <path> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  <query>                      Tree-sitter query string (positional, required)
  --root <path>                Root directory (required unless --file used)
  --file <path>                Explicit file to search (repeatable)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --language <name>            Language override (auto-detected if omitted)
  --max-matches <n>            Max total matches to return
  --languages                  List available/unavailable grammar packages

Examples:
  skill.ps1 run "(function_definition name: (identifier) @name)" --root ./src --glob "*.py"
  '{"query":"(function_definition name: (identifier) @name)","root":"/path","globs":["*.py"]}' | skill.ps1 run --stdin

Execution backend: aux find (aux-skills CLI)
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
        Write-Warning "warn: tree-sitter not installed (find unavailable). Install with: pip install 'aux-skills[query]'"
    }

    # Delegate to CLI doctor for full dependency check
    & aux doctor
}

function Get-Schema {
    & aux find --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux find --plan $plan
    } else {
        # CLI argument passthrough
        & aux find @Arguments
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
