#!/usr/bin/env pwsh
# aux meta-skill - Agent discovery and skill routing
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
aux - Agent discovery and skill routing meta-skill

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Not applicable (capabilities has no plan schema)
  run [--format names]         Emit skill registry (delegates to aux capabilities)

Usage (run):
  skill.ps1 run                 # Full JSON registry
  skill.ps1 run --format names  # Skill names only

Examples:
  skill.ps1 run
  skill.ps1 run --format names

Execution backend: aux capabilities (aux-skills CLI)
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
    Write-Output '{"note": "capabilities has no plan input — it takes only --format names|json"}'
}

function Invoke-Run {
    param([string[]]$Arguments)
    & aux capabilities @Arguments
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
