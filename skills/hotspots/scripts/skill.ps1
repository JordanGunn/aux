#!/usr/bin/env pwsh
# hotspots skill - Churn-weighted complexity hotspots per file (Tornhill-style)
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
hotspots - Churn-weighted complexity hotspots per file (Tornhill 2015)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  schema                       Emit JSON schema for plan input
  run [opts]                   Execute hotspot analysis

Usage (run):
  skill.ps1 run --root <path> [options]
  skill.ps1 run --stdin                           # Read plan JSON from stdin

Options:
  --root <path>                Repository root (required; may be subdir of repo)
  --glob <pattern>             Include glob (repeatable)
  --exclude <pattern>          Exclude glob (repeatable)
  --hidden                     Include hidden files
  --no-ignore                  Don't respect gitignore
  --since <spec>               Git log window start (default: "14 days ago")
                               Git-style: "30 days ago", "2025-01-01", "all"
  --until <spec>               Git log window end (default: now)
  --min-commits <n>            Minimum commit count to include a file (default: 2)
  --max-results <n>            Cap on ranked file list (post-sort)
  --percentile <p>             Quadrant cutoff percentile (default: 0.75)

Examples:
  skill.ps1 run --root ./
  skill.ps1 run --root ./ --since "30 days ago"
  skill.ps1 run --root ./ --since all --min-commits 5
  skill.ps1 run --root ./ --max-results 20
  '{"root":"./","since":"all"}' | skill.ps1 run --stdin

Execution backend: aux hotspots (aux-skills CLI)
"@
}

function Test-Validate {
    if (-not (Get-Command aux -ErrorAction SilentlyContinue)) {
        Write-Error "error: aux CLI not found. Install with: pip install aux-skills"
        exit 1
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "error: git not found. Install git and ensure it is in PATH"
        exit 1
    }

    # Delegate to CLI doctor for full dependency check
    & aux doctor
}

function Get-Schema {
    & aux hotspots --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux hotspots --plan $plan
    } else {
        # CLI argument passthrough
        & aux hotspots @Arguments
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
