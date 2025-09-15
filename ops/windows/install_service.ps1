param(
    [string]$RepoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..")).Path,
    [string]$ServiceName = "RoseService"
)

# Self-elevate if not running as admin
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Elevating permissions to Administrator..."
    
    # Build the arguments list properly
    $arguments = "-ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`""
    $arguments += " -RepoRoot `"$RepoRoot`""
    $arguments += " -ServiceName `"$ServiceName`""
    
    Write-Host "Starting elevated process with arguments: $arguments"
    Start-Process powershell -ArgumentList $arguments -Verb RunAs -Wait
    exit $LASTEXITCODE
}

Write-Host "Running with administrator privileges..." -ForegroundColor Green

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
    sc.exe stop $ServiceName 2>$null | Out-Null
    Start-Sleep -Milliseconds 500
    sc.exe delete $ServiceName 2>$null | Out-Null
    Start-Sleep -Milliseconds 500
} catch {}

# Create & start service
Write-Host "Creating service..."
sc.exe create $ServiceName binPath= "$BinPath" start= auto 2>$null | Out-Null
sc.exe description $ServiceName "Rose Takeover Server (listens on http://127.0.0.1:8765)" 2>$null | Out-Null

Write-Host "Starting service..."
sc.exe start $ServiceName 2>$null | Out-Null

Write-Host "Service status:"
sc.exe query $ServiceName

Write-Host "Installation completed successfully!"