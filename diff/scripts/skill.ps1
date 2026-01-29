#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir 'src'
$SkillDir = Split-Path -Parent $ScriptDir
$RootDir = Split-Path -Parent (Split-Path -Parent $SkillDir)

$AssetsDir = Join-Path $SkillDir 'assets'
$SchemasDir = Join-Path $AssetsDir 'schemas'

function Show-Help {
    @"
diff - Deterministic git diff inspection (bounded summary + optional patch)

Commands:
  help                         Show this help message
  validate                     Verify the skill is runnable (read-only)
  discover [opts]              Run discovery phase (enumerate change candidates)
  run [opts]                   Execute a bounded diff

Options (discover/run):
  --stdin                      Read plan JSON from stdin
"@
}

function Invoke-Validate {
    $errors = 0

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Error "error: uv not found. Install from https://docs.astral.sh/uv/"
        $errors++
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        Write-Error "error: git not found"
        $errors++
    }

    if (-not (Test-Path (Join-Path $SrcDir 'pyproject.toml'))) {
        Write-Error "error: missing $SrcDir/pyproject.toml"
        $errors++
    }

    if (-not (Test-Path (Join-Path $SrcDir 'cli.py'))) {
        Write-Error "error: missing $SrcDir/cli.py"
        $errors++
    }

    if (-not (Test-Path (Join-Path $SchemasDir 'diff_plan_v1.schema.json'))) {
        Write-Error "error: missing $SchemasDir/diff_plan_v1.schema.json"
        $errors++
    }

    if (-not (Test-Path (Join-Path $SchemasDir 'diff_summary_v1.schema.json'))) {
        Write-Error "error: missing $SchemasDir/diff_summary_v1.schema.json"
        $errors++
    }

    if (-not (Test-Path (Join-Path $SchemasDir 'diff_receipt_v1.schema.json'))) {
        Write-Error "error: missing $SchemasDir/diff_receipt_v1.schema.json"
        $errors++
    }

    if ($errors -gt 0) {
        exit 1
    }

    & uv run -q --no-progress --project $SrcDir python (Join-Path $SrcDir 'cli.py') validate
    if ($LASTEXITCODE -ne 0) { exit 1 }

    Write-Output "ok: diff skill is runnable"
}

function Invoke-Discover {
    param([string[]]$Args)
    & uv run -q --no-progress --project $SrcDir python (Join-Path $SrcDir 'cli.py') discover @Args
}

function Invoke-Run {
    param([string[]]$Args)
    & uv run -q --no-progress --project $SrcDir python (Join-Path $SrcDir 'cli.py') run @Args
}

$command = if ($args.Count -gt 0) { $args[0] } else { 'help' }
$remaining = if ($args.Count -gt 1) { $args[1..($args.Count - 1)] } else { @() }

switch ($command) {
    'help' { Show-Help }
    'validate' { Invoke-Validate }
    'discover' { Invoke-Discover -Args $remaining }
    'run' { Invoke-Run -Args $remaining }
    default {
        Write-Error "error: unknown command '$command'"
        Write-Output "run 'diff help' for usage"
        exit 1
    }
}
