#!/usr/bin/env pwsh
# grep skill - Agent-assisted text search
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
grep - Agent-assisted text search (deterministic ripgrep wrapper)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts] <pattern>         Execute a deterministic text search

Usage (run):
  skill.ps1 run <pattern> --root <path> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  <pattern>                    Search pattern (positional, required)
  --root <path>                Root directory (required)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --case <smart|sensitive|insensitive>  Case behavior (default: smart)
  --context <n>                Lines of context (default: 0)
  --max-matches <n>            Max matches to return
  --fixed                      Treat pattern as literal (default: regex)
  --hidden                     Search hidden files
  --no-ignore                  Don't respect gitignore

Examples:
  skill.ps1 run "TODO|FIXME" --root ./src --glob "*.py"
  skill.ps1 run "oauth" --root /path --case insensitive
  '{"root":"/path","patterns":[{"kind":"regex","value":"auth"}]}' | skill.ps1 run --stdin

Execution backend: aux grep (aux-skills CLI)
"@
}

function Test-Validate {
    if (-not (Get-Command aux -ErrorAction SilentlyContinue)) {
        Write-Error "error: aux CLI not found. Install with: pip install aux-skills"
        exit 1
    }

    # Delegate to CLI doctor for full dependency check
    & aux doctor
}

function Get-Schema {
    & aux grep --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux grep --plan $plan
    } else {
        # CLI argument passthrough
        & aux grep @Arguments
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
