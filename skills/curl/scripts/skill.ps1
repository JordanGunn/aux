#!/usr/bin/env pwsh
# curl skill - Agent-optimised HTTP fetch with progressive disclosure
# Invokes the aux CLI as the execution backend
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SkillDir = Split-Path -Parent $ScriptDir

function Show-Help {
    @"
curl - Agent-optimised HTTP fetch with progressive disclosure

Commands:
  help                         Show this help message
  init                         Emit all skill reference docs (concatenated)
  validate                     Verify the skill is runnable (checks aux + httpx)
  schema                       Emit JSON schema for plan input
  run [opts] <url>             Fetch a URL and return clean extracted content

Usage (run):
  skill.ps1 run <url> [options]
  skill.ps1 run --stdin                          # Read plan JSON from stdin

Options:
  <url>                        URL to fetch (positional)
  --method <GET|POST|...>      HTTP method (default: GET)
  --header <KEY:VALUE>         Request header (repeatable)
  --body <text>                Request body for POST/PUT/PATCH
  --mode <auto|text|markdown|json|raw>  Extraction mode (default: auto)
  --offset <n>                 Character offset for progressive disclosure (default: 0)
  --length <n>                 Characters to return from offset (default: 20000)
  --timeout <seconds>          Request timeout (default: 30.0)
  --no-follow-redirects        Do not follow HTTP redirects

Examples:
  skill.ps1 run https://docs.python.org/3/ --mode text
  skill.ps1 run https://api.example.com/data --mode json
  skill.ps1 run https://example.com --offset 20000
  '{"urls":["https://httpbin.org/json"],"mode":"json"}' | skill.ps1 run --stdin

Execution backend: aux curl (aux-skills CLI)
"@
}

function Invoke-Init {
    $RefsDir = Join-Path $SkillDir "references"
    $idx = 1

    Write-Output "# References"
    Write-Output ""
    Get-ChildItem "$RefsDir\[0-9][0-9]_*.md" | Sort-Object Name | ForEach-Object {
        if ($_.Name -eq "00_ROUTER.md") { return }
        $name = $_.BaseName -replace '^\d+_', ''
        $desc = (Select-String -Path $_.FullName -Pattern '^description:' -ErrorAction SilentlyContinue |
                 Select-Object -First 1)?.Line -replace '^description:\s*', ''
        Write-Output "${idx}. **${name}** — ${desc}"
        $idx++
    }
    Write-Output ""
    Write-Output "---"
    Write-Output ""

    Get-ChildItem "$RefsDir\[0-9][0-9]_*.md" | Sort-Object Name | ForEach-Object {
        if ($_.Name -eq "00_ROUTER.md") { return }
        Get-Content $_.FullName
        Write-Output ""
    }
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
    & aux curl --schema
}

function Invoke-Run {
    param([string[]]$Arguments)
    if ($Arguments.Count -gt 0 -and $Arguments[0] -eq "--stdin") {
        # Plan-based invocation: read JSON from stdin
        $plan = $input | Out-String
        & aux curl --plan $plan
    } else {
        # CLI argument passthrough
        & aux curl @Arguments
    }
}

$command = if ($args.Count -gt 0) { $args[0] } else { "help" }

switch ($command) {
    "help"     { Show-Help }
    "init"     { Invoke-Init }
    "validate" { Test-Validate }
    "schema"   { Get-Schema }
    "run"      { Invoke-Run -Arguments ($args | Select-Object -Skip 1) }
    default {
        Write-Error "error: unknown command '$command'"
        Write-Error "run 'skill.ps1 help' for usage"
        exit 1
    }
}
