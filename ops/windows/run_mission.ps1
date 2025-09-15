param(
    [Parameter(Mandatory=$true)]
    [string]$MissionPath
)

# Resolve project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path

# Prefer venv python
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python.exe"
}

Write-Host "Repo root: $RepoRoot"
Write-Host "Python:   $Python"
Write-Host "Mission:  $MissionPath"

# Run the mission in the current user’s interactive session
& $Python -m core.agent --mission $MissionPath
exit $LASTEXITCODE