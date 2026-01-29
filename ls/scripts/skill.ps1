#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir "src"
$SkillDir = Split-Path -Parent $ScriptDir
$RootDir = Resolve-Path (Join-Path $SkillDir "../..")

$AssetsDir = Join-Path $SkillDir "assets"
$SchemasDir = Join-Path $AssetsDir "schemas"

function Show-Help {
    @"
ls - Deterministic directory state inspection (bounded inventory + ranking)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  run [opts]                   Execute a deterministic directory inventory

Options (run):
  --stdin                      Read plan JSON from stdin (ls_plan_v1)
"@
}

function Test-Validate {
    $errors = 0

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Error "error: uv not found. Install from https://docs.astral.sh/uv/"
        $errors++
    }

    $pyproject = Join-Path $SrcDir "pyproject.toml"
    if (-not (Test-Path $pyproject)) {
        Write-Error "error: missing $pyproject"
        $errors++
    }

    $cli = Join-Path $SrcDir "cli.py"
    if (-not (Test-Path $cli)) {
        Write-Error "error: missing $cli"
        $errors++
    }

    $validator = Join-Path $SrcDir "validate.py"
    if (-not (Test-Path $validator)) {
        Write-Error "error: missing $validator"
        $errors++
    }

    $config = Join-Path $AssetsDir "ls_config_v1.json"
    if (-not (Test-Path $config)) {
        Write-Error "error: missing $config"
        $errors++
    }

    $configSchema = Join-Path $SchemasDir "ls_config_v1.schema.json"
    if (-not (Test-Path $configSchema)) {
        Write-Error "error: missing $configSchema"
        $errors++
    }

    $planSchema = Join-Path $SchemasDir "ls_plan_v1.schema.json"
    if (-not (Test-Path $planSchema)) {
        Write-Error "error: missing $planSchema"
        $errors++
    }

    $resultSchema = Join-Path $SchemasDir "ls_result_bundle_v1.schema.json"
    if (-not (Test-Path $resultSchema)) {
        Write-Error "error: missing $resultSchema"
        $errors++
    }

    $auxLsDir = Join-Path $RootDir ".aux/ls"
    if (-not (Test-Path $auxLsDir)) {
        Write-Error "error: missing directory $auxLsDir"
        $errors++
    }

    if ($errors -gt 0) {
        exit 1
    }

    # Fail-closed asset/config validation.
    & uv run -q --no-progress --project $SrcDir python $validator
    & uv run -q --no-progress --project $SrcDir python $cli validate

    Write-Output "ok: ls skill is runnable"
}

function Invoke-Run {
    param([string[]]$Arguments)
    $cli = Join-Path $SrcDir "cli.py"
    & uv run -q --no-progress --project $SrcDir python $cli run @Arguments
}

$command = if ($args.Count -gt 0) { $args[0] } else { "help" }

switch ($command) {
    "help" { Show-Help }
    "validate" { Test-Validate }
    "run" { Invoke-Run -Arguments ($args | Select-Object -Skip 1) }
    default {
        Write-Error "error: unknown command '$command'"
        Write-Error "run 'ls help' for usage"
        exit 1
    }
}
