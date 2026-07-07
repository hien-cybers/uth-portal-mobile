param(
    [switch]$all,
    [string]$id,
    [string]$function,
    [string]$tag,
    [string]$type,
    [double]$delay = 0,
    [double]$stepDelay = 0,
    [switch]$validate,
    [switch]$allowNonTestEnvironment
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

$ArgsList = @("-m", "tests.runner")
if ($all) { $ArgsList += "--all" }
if ($id) { $ArgsList += @("--id", $id) }
if ($function) { $ArgsList += @("--function", $function) }
if ($tag) { $ArgsList += @("--tag", $tag) }
if ($type) { $ArgsList += @("--type", $type) }
if ($delay -gt 0) { $ArgsList += @("--delay", "$delay") }
if ($stepDelay -gt 0) { $ArgsList += @("--step-delay", "$stepDelay") }
if ($validate) { $ArgsList += "--validate" }
if ($allowNonTestEnvironment) { $ArgsList += "--allow-non-test-environment" }

Push-Location $RepoRoot
try {
    & $Python @ArgsList
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
