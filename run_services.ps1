# Windows PowerShell script to run the distributed services
# This script is compatible with Windows environments

Write-Host "Starting Distributed Services for Windows..." -ForegroundColor Cyan

# Stop any existing services
Write-Host "Stopping any existing services..."
if (Test-Path "stop_services.ps1") {
    & .\stop_services.ps1
} else {
    # Fallback to manual process termination
    Write-Host "Stopping Python processes..."
    $authProcesses = Get-Process -Name python* -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*app.main*" }
    if ($authProcesses) {
        $authProcesses | ForEach-Object { Stop-Process -Id $_.Id -Force }
        Write-Host "Python processes stopped."
    } else {
        Write-Host "No Python processes found to stop."
    }
}

# Function to check if a port is in use and kill the process if needed
function Check-Port {
    param (
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        Write-Host "Port $Port is in use. Killing the process..." -ForegroundColor Yellow
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Killing process: $($process.Name) (PID: $($process.Id))"
                Stop-Process -Id $process.Id -Force
            }
        }
        Start-Sleep -Seconds 1
    }
}

# Check if ports are in use
Check-Port -Port 8080
Check-Port -Port 8081

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    & $venvPath
} else {
    Write-Host "Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Please create a virtual environment first with: python -m venv venv" -ForegroundColor Red
    exit 1
}

# Create logs directory if it doesn't exist
if (-not (Test-Path "logs")) {
    New-Item -Path "logs" -ItemType Directory | Out-Null
}

# Clear previous log files
Remove-Item -Path "logs\*.log" -ErrorAction SilentlyContinue

# Start Authentication Service
Write-Host "Starting Authentication Service on port 8080..." -ForegroundColor Cyan
$env:AUTHENTICATION_PORT = 8080
$authJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\auth_service
    $env:AUTHENTICATION_PORT = $using:env:AUTHENTICATION_PORT
    python -m app.main 
} 
$authPid = $authJob.Id
$authPid | Out-File -FilePath "auth_service.pid"
Write-Host "Authentication Service started with Job ID: $authPid"

# Start Transaction Service
Write-Host "Starting Transaction Service on port 8081..." -ForegroundColor Cyan
$env:TRANSACTION_PORT = 8081
$transJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\transaction_service
    $env:TRANSACTION_PORT = $using:env:TRANSACTION_PORT
    python -m app.main
} 
$transPid = $transJob.Id
$transPid | Out-File -FilePath "transaction_service.pid"
Write-Host "Transaction Service started with Job ID: $transPid"

# Wait for services to start
Write-Host "Waiting for services to initialize (10 seconds)..." -ForegroundColor Cyan
Start-Sleep -Seconds 10

# Test if Authentication Service is responsive
Write-Host "Testing Authentication Service..." -ForegroundColor Cyan
try {
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8080/docs" -UseBasicParsing
    Write-Host "Authentication Service responded with HTTP code: $($authResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Authentication Service failed to start properly!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    
    # Display log contents
    Write-Host "Authentication Service logs:" -ForegroundColor Yellow
    Receive-Job -Job $authJob
    
    # Stop services
    if (Test-Path "stop_services.ps1") {
        & .\stop_services.ps1
    }
    exit 1
}

# Test if Transaction Service is responsive
Write-Host "Testing Transaction Service..." -ForegroundColor Cyan
try {
    $transResponse = Invoke-WebRequest -Uri "http://localhost:8081/docs" -UseBasicParsing
    Write-Host "Transaction Service responded with HTTP code: $($transResponse.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "Transaction Service failed to start properly!" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    
    # Display log contents
    Write-Host "Transaction Service logs:" -ForegroundColor Yellow
    Receive-Job -Job $transJob
    
    # Stop services
    if (Test-Path "stop_services.ps1") {
        & .\stop_services.ps1
    }
    exit 1
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Services are running!" -ForegroundColor Green
Write-Host "Authentication Service: http://localhost:8080" -ForegroundColor Cyan
Write-Host "Transaction Service: http://localhost:8081" -ForegroundColor Cyan
Write-Host ""
Write-Host "Example authentication:" -ForegroundColor Yellow
Write-Host "Invoke-WebRequest -Uri 'http://localhost:8080/token' -Method 'POST' -ContentType 'application/x-www-form-urlencoded' -Body 'username=admin&password=admin' | ConvertFrom-Json" -ForegroundColor Yellow
Write-Host ""
Write-Host "Using the token with Transaction Service:" -ForegroundColor Yellow
Write-Host "Invoke-WebRequest -Uri 'http://localhost:8081/transactions' -Method 'GET' -Headers @{Authorization = 'Bearer YOUR_TOKEN_HERE'} | ConvertFrom-Json" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop the services, run: .\stop_services.ps1" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Green 