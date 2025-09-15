param(
    [string]$RepoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..")).Path,
    [string]$ServiceName = "RoseService"
)

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) { $Python = $VenvPython } else { $Python = "python.exe" }

$BinPath = "`"$Python`" `"$RepoRoot\core\rose_service.py`""

Write-Host "Installing service $ServiceName with commanmd:"
Write-Host $BinPath

# Remove the Old Service if it exists
sc.exe query $ServiceName | Out-Null
if ($LASTEXITCODE -eq 0) {
    sc.exe stop $ServiceName | Out-Null
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 1
}

sc.exe create $ServiceName binPath= $BinPath start= auto | Out-Null
sc.exe description $ServiceName "Rose Takeover Server (localhost:8765)" | Out-Null

sc.exe start $ServiceName | Out-Null
sc.exe query $ServiceName
