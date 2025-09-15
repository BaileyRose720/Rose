if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Start-Process powershell -ArgumentList $arguments -Verb RunAs -Wait
    exit $LASTEXITCODE
}

param(
    [string]$RepoRoot = (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..")).Path,
    [string]$ServiceName = "RoseService"
)

# Run as administrator check
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Error "This script must be run as Administrator. Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

# Prefer venv Python if present
$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
    Write-Host "Using virtual environment Python: $Python"
} else {
    $Python = "python.exe"
    Write-Host "Using system Python"
}

# Verify Python exists
if (-not (Test-Path $Python) -and $Python -eq $VenvPython) {
    Write-Error "Python executable not found at: $Python"
    Write-Error "Please create the virtual environment first: python -m venv .venv"
    exit 1
}

# Verify service script exists
$ServiceScript = Join-Path $RepoRoot "core\rose_service.py"
if (-not (Test-Path $ServiceScript)) {
    Write-Error "Service script not found at: $ServiceScript"
    exit 1
}

# Command that the service runs
$BinPath = "`"$Python`" `"$ServiceScript`""

Write-Host "Installing service $ServiceName with command:"
Write-Host $BinPath

# Check if service exists first
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($service) {
    Write-Host "Service already exists, stopping and removing..."
    try {
        # Stop service if running
        if ($service.Status -eq 'Running') {
            Stop-Service -Name $ServiceName -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
        }
        
        # Delete service
        sc.exe delete $ServiceName | Out-Null
        Start-Sleep -Seconds 1
        
        # Verify service was removed
        $serviceCheck = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        if ($serviceCheck) {
            Write-Error "Failed to remove existing service. Please remove it manually."
            exit 1
        }
        
        Write-Host "Old service removed successfully."
    }
    catch {
        Write-Error "Error removing existing service: $_"
        exit 1
    }
}

# Create service
Write-Host "Creating new service..."
try {
    $createResult = sc.exe create $ServiceName binPath= "$BinPath" start= auto
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create service: $createResult"
        exit 1
    }
    
    # Add description
    sc.exe description $ServiceName "Rose Takeover Server (listens on http://127.0.0.1:8765)" | Out-Null
    
    Write-Host "Service created successfully."
}
catch {
    Write-Error "Error creating service: $_"
    exit 1
}

# Start service
Write-Host "Starting service..."
try {
    Start-Service -Name $ServiceName -ErrorAction Stop
    Write-Host "Service started successfully."
}
catch {
    Write-Error "Error starting service: $_"
    Write-Host "Trying alternative start method..."
    sc.exe start $ServiceName | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to start service using sc.exe"
    }
}

# Verify service status
Write-Host "Service status:"
try {
    Get-Service -Name $ServiceName | Format-Table Name, Status, StartType -AutoSize
}
catch {
    Write-Warning "Could not query service status: $_"
}

Write-Host "Installation completed."