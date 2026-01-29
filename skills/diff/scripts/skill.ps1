#!/usr/bin/env pwsh
# diff skill - Deterministic file/directory comparison
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
diff - Deterministic file/directory comparison

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute a file/directory comparison

Options (run):
  <path_a> <path_b>            Paths to compare
  --context <n>                Lines of context (default: 3)
  --ignore-whitespace          Ignore whitespace differences
  --ignore-case                Ignore case differences
  --stdin                      Read plan JSON from stdin

Execution backend: aux diff (aux-skills CLI)
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
    & aux diff --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux diff --plan $plan
    } else {
        # CLI argument passthrough
        & aux diff @Arguments
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
