param(
    [Parameter(Mandatory=$true)]
    [string]$MissionPath
)

# Resolve Project Root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..") | Select-Object -ExpandProperty Path

# Preference for venv python, fallbacking to system
$VenvPython = Join-Path $RepoRoot "venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python.exe"
}

Write-Host "Running mission $MissionPath with $Python"

& $Python -m core.agent --mission $MissionPath
exit $LASTEXITCODE