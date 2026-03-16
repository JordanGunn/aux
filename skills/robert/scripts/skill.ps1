#!/usr/bin/env pwsh
# robert skill - Robert C. Martin package design metrics
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
robert - Robert C. Martin package design metrics (coupling, abstractness, main sequence)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute package design metrics analysis

Usage (run):
  skill.ps1 run --root <path> --language <go|python> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Root directory (required)
  --language <go|python>       Language to analyze (required)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --max-results <n>            Max packages in output
  --include-main               Go only: include 'package main' packages

Examples:
  skill.ps1 run --root ./src --language python
  skill.ps1 run --root ./src --language go --include-main
  '{"root":"/path","language":"go"}' | skill.ps1 run --stdin

Execution backend: aux robert (aux-skills CLI)
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
        Write-Warning "warn: tree-sitter not installed (AST abstractness detection unavailable; regex fallback will run). Install with: pip install 'aux-skills[query]'"
    }

    # Delegate to CLI doctor for full dependency check
    & aux doctor
}

function Get-Schema {
    & aux robert --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux robert --plan $plan
    } else {
        # CLI argument passthrough
        & aux robert @Arguments
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
