param(
    [string]$RepoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..")).Path,
    [string]$ServiceName = "RoseService"
)

# Prefer venv Python if present
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python.exe"
}

# Command that the service runs (ONLY the Takeover server – no UI automation here)
$BinPath = "`"$Python`" `"$RepoRoot\core\rose_service.py`""

Write-Host "Installing service $ServiceName with command:"
Write-Host $BinPath

# Best-effort cleanup without throwing
try {
    sc.exe stop $ServiceName | Out-Null
    Start-Sleep -Milliseconds 500
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Milliseconds 500
} catch {}

# Create & start service
sc.exe create $ServiceName binPath= $BinPath start= auto | Out-Null
sc.exe description $ServiceName "Rose Takeover Server (listens on http://127.0.0.1:8765)" | Out-Null
sc.exe start $ServiceName | Out-Null
sc.exe query $ServiceName