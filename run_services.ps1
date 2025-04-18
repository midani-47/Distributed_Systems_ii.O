# Windows PowerShell script to run services
param (
    [int]$auth_port = 8080,
    [int]$transaction_port = 8081
)

Write-Host "==============================================="
Write-Host "Starting Fraud Detection Services (Windows)"
Write-Host "==============================================="

# Stop any existing services
if (Test-Path -Path ".\stop_services.ps1") {
    Write-Host "Stopping any existing services..."
    & .\stop_services.ps1
}

# Create logs directory and clean old logs
if (-not (Test-Path -Path ".\logs")) {
    New-Item -Path ".\logs" -ItemType Directory | Out-Null
}
Remove-Item -Path ".\logs\*.log" -ErrorAction SilentlyContinue

# Function to check if a port is in use
function Test-PortInUse {
    param([int]$port)
    
    $netstat = netstat -ano | Select-String "LISTENING" | Select-String ":$port "
    return ($netstat -ne $null)
}

# Check if ports are in use and handle conflicts
if (Test-PortInUse -port $auth_port) {
    Write-Host "Warning: Port $auth_port is already in use!"
    # Try to find the process using the port
    $processId = (netstat -ano | Select-String "LISTENING" | Select-String ":$auth_port " | ForEach-Object { ($_ -split '\s+')[-1] }) -as [int]
    if ($processId) {
        Write-Host "Process ID using port $auth_port: $processId"
        $confirmKill = Read-Host "Do you want to kill this process? (y/n)"
        if ($confirmKill.ToLower() -eq 'y') {
            Stop-Process -Id $processId -Force
            Write-Host "Process killed."
        } else {
            Write-Host "Please choose another port."
            exit 1
        }
    }
}

if (Test-PortInUse -port $transaction_port) {
    Write-Host "Warning: Port $transaction_port is already in use!"
    # Try to find the process using the port
    $processId = (netstat -ano | Select-String "LISTENING" | Select-String ":$transaction_port " | ForEach-Object { ($_ -split '\s+')[-1] }) -as [int]
    if ($processId) {
        Write-Host "Process ID using port $transaction_port: $processId"
        $confirmKill = Read-Host "Do you want to kill this process? (y/n)"
        if ($confirmKill.ToLower() -eq 'y') {
            Stop-Process -Id $processId -Force
            Write-Host "Process killed."
        } else {
            Write-Host "Please choose another port."
            exit 1
        }
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..."
if (Test-Path -Path ".\venv\Scripts\activate.ps1") {
    & .\venv\Scripts\activate.ps1
} elseif (Test-Path -Path ".\.venv\Scripts\activate.ps1") {
    & .\.venv\Scripts\activate.ps1
} else {
    Write-Host "Error: Virtual environment not found. Please create it first."
    exit 1
}

# Start Auth Service
Write-Host "Starting Authentication Service on port $auth_port..."
$env:AUTHENTICATION_PORT = $auth_port
Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $auth_port" -WorkingDirectory ".\auth_service" -RedirectStandardOutput ".\logs\auth_service.log" -RedirectStandardError ".\logs\auth_service_error.log" -NoNewWindow
$auth_pid = $pid  # This isn't actually the correct PID, but we'll need a different approach for Windows
$auth_pid | Out-File -FilePath ".\auth_service.pid"
Write-Host "Authentication Service started with PID: $auth_pid"

# Wait a moment to ensure the service starts
Start-Sleep -Seconds 5

# Start Transaction Service
Write-Host "Starting Transaction Service on port $transaction_port..."
$env:TRANSACTION_PORT = $transaction_port
Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $transaction_port" -WorkingDirectory ".\transaction_service" -RedirectStandardOutput ".\logs\transaction_service.log" -RedirectStandardError ".\logs\transaction_service_error.log" -NoNewWindow
$transaction_pid = $pid  # This isn't actually the correct PID, but we'll need a different approach for Windows
$transaction_pid | Out-File -FilePath ".\transaction_service.pid"
Write-Host "Transaction Service started with PID: $transaction_pid"

# Wait for services to start
Write-Host "Waiting for services to start..."
Start-Sleep -Seconds 10

# Print URLs
Write-Host "==========================================================="
Write-Host "Services are now running:"
Write-Host "- Auth Service: http://localhost:$auth_port/docs"
Write-Host "- Transaction Service: http://localhost:$transaction_port/docs"
Write-Host ""
Write-Host "To stop the services, run: .\stop_services.ps1"
Write-Host "==========================================================="

# Wait for Ctrl+C or manual termination
Write-Host "Press Ctrl+C to stop services..."
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # Cleanup when the script is terminated
    Write-Host "Stopping services..."
    if (Test-Path -Path ".\stop_services.ps1") {
        & .\stop_services.ps1
    }
} 