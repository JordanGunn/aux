#!/usr/bin/env pwsh
# prune skill - Tiered dead code candidate audit
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
prune - Tiered dead code candidate audit (advisory — requires human verification)

ADVISORY: Output is static analysis only. Never act on prune results without
running ``aux usages`` to verify each candidate and reviewing the code.

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a prune audit

Usage (run):
  skill.ps1 run --root <path> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Root directory (required)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --scope <scope>              Analysis scope: 'symbols' or 'files' (repeatable; default: symbols)
  --language <name>            Tree-sitter language override (symbols scope)
  --min-name-length <n>        Skip symbols shorter than N chars (default: 4)
  --max-refs <n>               Flag candidates with <= N external refs (default: 0)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --max-symbols <n>            Cap on symbols analyzed

Examples:
  skill.ps1 run --root ./src --glob "**/*.py"
  skill.ps1 run --root ./src --glob "**/*.py" --scope files
  '{"root":"/path","globs":["**/*.py"],"scope":["symbols"]}' | skill.ps1 run --stdin

Execution backend: aux prune (aux-skills CLI)
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
        Write-Warning "warn: tree-sitter not installed (symbols scope unavailable). Install with: pip install 'aux-skills[query]'"
        Write-Warning "warn: use --scope files for text-only analysis without tree-sitter"
    }

    # Delegate to CLI doctor for full dependency check
    & aux doctor
}

function Get-Schema {
    & aux prune --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux prune --plan $plan
    } else {
        # CLI argument passthrough
        & aux prune @Arguments
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
