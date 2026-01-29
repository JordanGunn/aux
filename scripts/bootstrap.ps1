$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

$Skills = @("grep", "find", "diff", "ls")

Write-Output "aux: bootstrapping all skills..."
Write-Output ""

$failed = 0

foreach ($skill in $Skills) {
    $bootstrapScript = Join-Path $RootDir "$skill/bootstrap.ps1"
    if (Test-Path $bootstrapScript) {
        Write-Output "--- $skill ---"
        try {
            & $bootstrapScript
            Write-Output ""
        } catch {
            Write-Error "error: $skill bootstrap failed"
            $failed++
            Write-Output ""
        }
    } else {
        Write-Warning "warning: $skill/bootstrap.ps1 not found, skipping"
        Write-Output ""
    }
}

if ($failed -gt 0) {
    Write-Output "aux: $failed skill(s) failed to bootstrap"
    exit 1
}

Write-Output "aux: all skills bootstrapped successfully"
