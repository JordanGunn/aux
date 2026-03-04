#!/usr/bin/env pwsh
# rename skill - Move/rename files and directories
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
rename - Move/rename files and directories

Commands:
  help                   Show this help message
  validate               Verify the skill is runnable
  schema                 Emit JSON schema for plan input
  run [opts]             Execute a rename (dry-run by default)

Usage (run):
  skill.ps1 run --stdin [--apply]            # Read plan JSON from stdin
  skill.ps1 run <src> <dst>                  # Simple mode

Two-phase execution:
  Phase 1: skill.ps1 run --stdin             -> dry-run preview, no writes
  Phase 2: skill.ps1 run --stdin --apply     -> apply moves

Examples:
  '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' | skill.ps1 run --stdin
  '{"moves":[{"src":"/path/old.py","dst":"/path/new.py"}]}' | skill.ps1 run --stdin --apply

Execution backend: aux rename (aux-skills CLI)
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
    & aux rename --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    $applyFlag = $Arguments -contains "--apply"
    $remaining = $Arguments | Where-Object { $_ -ne "--apply" }

    if ($remaining.Count -gt 0 -and $remaining[0] -eq "--stdin") {
        $plan = $input | Out-String
        if ($applyFlag) { & aux rename --plan $plan --apply }
        else { & aux rename --plan $plan }
    } else {
        if ($applyFlag) { & aux rename @remaining --apply }
        else { & aux rename @remaining }
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
