#!/usr/bin/env pwsh
# ccx skill - Cyclomatic + Cognitive Complexity per function (McCabe + Campbell)
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
ccx - Cyclomatic + Cognitive Complexity per function (McCabe 1976 + Campbell 2018)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute complexity analysis

Usage (run):
  skill.ps1 run --root <path> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Root directory (required)
  --language <lang>            Restrict to one language (repeatable)
                               Supported: python, javascript, typescript, go, rust, java
  --glob <pattern>             Override include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --max-results <n>            Max functions in output (post-sort cap)
  --min-ccx <n>                Filter — only return functions with ccx >= n (default: 1)

Examples:
  skill.ps1 run --root ./src
  skill.ps1 run --root ./src --language python --min-ccx 11
  skill.ps1 run --root ./src --max-results 20
  '{"root":"./src","languages":["python"]}' | skill.ps1 run --stdin

Execution backend: aux ccx (aux-skills CLI)
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
    & aux ccx --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux ccx --plan $plan
    } else {
        # CLI argument passthrough
        & aux ccx @Arguments
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
