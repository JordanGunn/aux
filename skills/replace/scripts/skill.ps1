#!/usr/bin/env pwsh
# replace skill - Focused fixed-string text replacement
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
replace - Focused fixed-string text replacement

Commands:
  help                   Show this help message
  validate               Verify the skill is runnable
  schema                 Emit JSON schema for plan input
  run [opts]             Execute a replacement (dry-run by default)

Usage (run):
  skill.ps1 run --stdin [--apply]            # Read plan JSON from stdin
  skill.ps1 run <old> <new> --root <path>    # Simple mode

Two-phase execution:
  Phase 1: skill.ps1 run --stdin             -> dry-run diff, no writes
  Phase 2: skill.ps1 run --stdin --apply     -> apply changes

Examples:
  '{"old":"parse_config","new":"load_config","root":"/repo","globs":["*.py"]}' | skill.ps1 run --stdin
  '{"old":"parse_config","new":"load_config","root":"/repo","globs":["*.py"]}' | skill.ps1 run --stdin --apply

Execution backend: aux replace (aux-skills CLI)
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
    & aux replace --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    $applyFlag = $Arguments -contains "--apply"
    $remaining = $Arguments | Where-Object { $_ -ne "--apply" }

    if ($remaining.Count -gt 0 -and $remaining[0] -eq "--stdin") {
        $plan = $input | Out-String
        if ($applyFlag) { & aux replace --plan $plan --apply }
        else { & aux replace --plan $plan }
    } else {
        if ($applyFlag) { & aux replace @remaining --apply }
        else { & aux replace @remaining }
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
