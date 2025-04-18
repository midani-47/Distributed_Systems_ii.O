#!/usr/bin/env pwsh
# Windows PowerShell script to run fraud detection services

# Set script to stop on first error
$ErrorActionPreference = "Stop"

Write-Host "`n=== Starting Fraud Detection Services ===`n" -ForegroundColor Cyan

# Define ports
$AUTH_PORT = 8080
$TRANSACTION_PORT = 8081

# Create logs directory
$logsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -Path $logsDir -ItemType Directory | Out-Null
    Write-Host "Created logs directory at $logsDir" -ForegroundColor Green
}

# First stop any running services to avoid conflicts
if (Test-Path "stop_services.ps1") {
    Write-Host "Stopping any running services..." -ForegroundColor Yellow
    & "$PSScriptRoot\stop_services.ps1"
}

# Function to check if a port is in use
function Test-PortInUse {
    param (
        [int]$Port
    )
    
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    return ($connections.Count -gt 0)
}

# Function to kill process using a specific port
function Stop-ProcessUsingPort {
    param (
        [int]$Port,
        [string]$ServiceName
    )
    
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    
    if ($connections) {
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Found process using port $Port: $($process.Name) (PID: $($process.Id))" -ForegroundColor Yellow
                Write-Host "Stopping process..." -NoNewline
                
                try {
                    Stop-Process -Id $process.Id -Force
                    Write-Host " Done" -ForegroundColor Green
                } catch {
                    Write-Host " Failed: $_" -ForegroundColor Red
                }
            }
        }
        
        # Verify port is now free
        Start-Sleep -Seconds 2
        if (Test-PortInUse -Port $Port) {
            Write-Host "Warning: Port $Port is still in use after attempting to free it." -ForegroundColor Red
            Write-Host "Please manually close the application using this port and try again." -ForegroundColor Red
            exit 1
        }
    }
}

# Check for port conflicts and resolve them
if (Test-PortInUse -Port $AUTH_PORT) {
    Write-Host "Port $AUTH_PORT is already in use." -ForegroundColor Yellow
    Stop-ProcessUsingPort -Port $AUTH_PORT -ServiceName "Authentication Service"
}

if (Test-PortInUse -Port $TRANSACTION_PORT) {
    Write-Host "Port $TRANSACTION_PORT is already in use." -ForegroundColor Yellow
    Stop-ProcessUsingPort -Port $TRANSACTION_PORT -ServiceName "Transaction Service"
}

# Activate virtual environment
$venvPath = Join-Path $PSScriptRoot "venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    Write-Host "Activating virtual environment..." -NoNewline
    & $activateScript
    Write-Host " Done" -ForegroundColor Green
} else {
    Write-Host "Virtual environment not found at $venvPath. Proceeding without activation." -ForegroundColor Yellow
}

# Clear previous log files
Get-ChildItem -Path $logsDir -Filter "*.log" | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | Remove-Item
Write-Host "Cleaned old log files" -ForegroundColor Green

# Set environment variables for both services
$env:AUTH_SERVICE_PORT = $AUTH_PORT
$env:TRANSACTION_SERVICE_PORT = $TRANSACTION_PORT
$env:PYTHONPATH = $PSScriptRoot

# Function to start a service
function Start-Service {
    param (
        [string]$Name,
        [string]$Command,
        [string]$WorkingDir,
        [string]$PidFile
    )
    
    Write-Host "Starting $Name..." -ForegroundColor Cyan
    
    Set-Location $WorkingDir
    
    # Start the process in the background
    $job = Start-Job -ScriptBlock {
        param($command, $workDir)
        Set-Location $workDir
        Invoke-Expression $command
    } -ArgumentList $Command, $WorkingDir
    
    # Save the job ID to the PID file
    $job.Id | Out-File -FilePath $PidFile
    
    # Wait a bit for the service to start
    Start-Sleep -Seconds 3
    
    # Check if the job is still running
    if (Get-Job -Id $job.Id -ErrorAction SilentlyContinue) {
        Write-Host "$Name started successfully (Job ID: $($job.Id))" -ForegroundColor Green
        return $true
    } else {
        Write-Host "$Name failed to start" -ForegroundColor Red
        return $false
    }
}

# Start Authentication Service
$authServiceDir = Join-Path $PSScriptRoot "auth_service"
$authCommand = "python -m app.main"
$authLogFile = Join-Path $logsDir "auth_service.log"
$authSucceeded = Start-Service -Name "Authentication Service" -Command $authCommand -WorkingDir $authServiceDir -PidFile "auth.pid"

# Start Transaction Service
$transServiceDir = Join-Path $PSScriptRoot "transaction_service"
$transCommand = "python -m app.main"
$transLogFile = Join-Path $logsDir "transaction_service.log"
$transSucceeded = Start-Service -Name "Transaction Service" -Command $transCommand -WorkingDir $transServiceDir -PidFile "transaction.pid"

# Display info about running services
Write-Host "`n=== Service Status ===`n" -ForegroundColor Cyan

if ($authSucceeded) {
    Write-Host "✅ Authentication Service: Running on http://localhost:$AUTH_PORT" -ForegroundColor Green
    Write-Host "   - API Documentation: http://localhost:$AUTH_PORT/docs" -ForegroundColor Gray
    Write-Host "   - Log file: $authLogFile" -ForegroundColor Gray
} else {
    Write-Host "❌ Authentication Service: Failed to start" -ForegroundColor Red
}

if ($transSucceeded) {
    Write-Host "✅ Transaction Service: Running on http://localhost:$TRANSACTION_PORT" -ForegroundColor Green
    Write-Host "   - API Documentation: http://localhost:$TRANSACTION_PORT/docs" -ForegroundColor Gray
    Write-Host "   - Log file: $transLogFile" -ForegroundColor Gray
} else {
    Write-Host "❌ Transaction Service: Failed to start" -ForegroundColor Red
}

if ($authSucceeded -and $transSucceeded) {
    Write-Host "`n✅ All services started successfully!" -ForegroundColor Green
    Write-Host "   - To test the services: .\test_services.ps1" -ForegroundColor Cyan
    Write-Host "   - To stop the services: .\stop_services.ps1" -ForegroundColor Cyan
} else {
    Write-Host "`n❌ Some services failed to start. Check the logs for details." -ForegroundColor Red
}

Write-Host "" 