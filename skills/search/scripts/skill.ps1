#!/usr/bin/env pwsh
# search skill - Hierarchical fd → rg [→ tree-sitter] pipeline
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
search - Hierarchical file-discovery + content-search [+ AST-structure] pipeline

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a search (plan mode only)

Usage (run):
  skill.ps1 run --stdin                           # Read plan JSON from stdin (required)

Note: search requires a full composite plan (surface + search sub-plans).
      Add a "structure" field for optional tier-3 tree-sitter AST matching.
      Use --schema to see the plan structure.

Examples:
  '{"root":"/path","surface":{"root":"/path","globs":["*.py"]},"search":{"root":"/path","patterns":[{"value":"TODO"}]}}' | skill.ps1 run --stdin

Execution backend: aux search (aux-skills CLI)
"@
}

function Test-Validate {
    if (-not (Get-Command aux -ErrorAction SilentlyContinue)) {
        Write-Error "error: aux CLI not found. Install with: pip install aux-skills"
        exit 1
    }
    & aux doctor
}

function Get-Schema {
    & aux search --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        $plan = $input | Out-String
        & aux search --plan $plan
    } else {
        Write-Error "error: search requires --stdin (plan mode only)"
        exit 1
    }
}

$command = if ($args.Count -gt 0) { $args[0] } else { "help" }

switch ($command) {
    "help"     { Show-Help }
    "validate" { Test-Validate }
    "schema"   { Get-Schema }
    "run"      { Invoke-Run -Arguments ($args | Select-Object -Skip 1) }
    default {
        Write-Error "error: unknown command '$command'"
        exit 1
    }
}
