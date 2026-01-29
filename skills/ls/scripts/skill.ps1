#!/usr/bin/env pwsh
# ls skill - Deterministic directory state inspection
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
ls - Deterministic directory state inspection (bounded inventory + ranking)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a deterministic directory inventory

Options (run):
  <path>                       Directory to list (default: .)
  --depth <n>                  Recursion depth (default: 1)
  --sort <name|size|time>      Sort order (default: name)
  --hidden                     Include hidden files
  --max-entries <n>            Max entries (default: 100)
  --stdin                      Read plan JSON from stdin

Execution backend: aux ls (aux-skills CLI)
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
    & aux ls --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux ls --plan $plan
    } else {
        # CLI argument passthrough
        & aux ls @Arguments
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
