#!/usr/bin/env pwsh
# find skill - Agent-assisted file enumeration
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
find - Agent-assisted file enumeration (deterministic fd wrapper)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a deterministic file enumeration

Options (run):
  --root <path>                Root directory (default: .)
  --glob <pattern>             Glob pattern for names (repeatable)
  --exclude <pattern>          Exclude pattern (repeatable)
  --type <file|directory|any>  Entry type (default: file)
  --max-depth <n>              Maximum directory depth
  --max-results <n>            Max results (default: 500)
  --hidden                     Include hidden files
  --stdin                      Read plan JSON from stdin

Execution backend: aux find (aux-skills CLI)
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
