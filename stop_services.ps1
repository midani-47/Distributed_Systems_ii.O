#!/usr/bin/env pwsh
# Windows PowerShell script to stop fraud detection services

# Set script to stop on first error
$ErrorActionPreference = "Stop"

Write-Host "`n=== Stopping Fraud Detection Services ===`n" -ForegroundColor Cyan

# Function to stop a service using its PID file
function Stop-ServiceWithPidFile {
    param (
        [string]$ServiceName,
        [string]$PidFile
    )
    
    if (Test-Path $PidFile) {
        try {
            $jobId = Get-Content $PidFile
            Write-Host "Stopping $ServiceName (Job ID: $jobId)..." -NoNewline
            
            # Try to stop the job
            if ($jobId -match '^\d+$') {
                if (Get-Job -Id $jobId -ErrorAction SilentlyContinue) {
                    Stop-Job -Id $jobId -ErrorAction SilentlyContinue
                    Remove-Job -Id $jobId -Force -ErrorAction SilentlyContinue
                    Write-Host " Done" -ForegroundColor Green
                } else {
                    Write-Host " Job not found" -ForegroundColor Yellow
                }
            } else {
                Write-Host " Invalid job ID in PID file" -ForegroundColor Yellow
            }
            
            # Remove the PID file
            Remove-Item $PidFile -Force
        } catch {
            Write-Host " Failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "$ServiceName is not running (no PID file found)" -ForegroundColor Yellow
    }
}

# Kill any Python processes running our services
function Stop-PythonProcesses {
    # Get all Python processes
    $pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue
    
    if ($pythonProcesses) {
        Write-Host "Checking for Python processes running our services..." -ForegroundColor Yellow
        
        foreach ($process in $pythonProcesses) {
            # Get command line for the process to identify our services
            try {
                $cmdline = (Get-WmiObject Win32_Process -Filter "ProcessId = $($process.Id)").CommandLine
                
                # Check if this is one of our services
                if ($cmdline -match "app\.main" -and ($cmdline -match "auth_service" -or $cmdline -match "transaction_service")) {
                    Write-Host "Stopping Python process with ID $($process.Id)..." -NoNewline
                    try {
                        Stop-Process -Id $process.Id -Force
                        Write-Host " Done" -ForegroundColor Green
                    } catch {
                        Write-Host " Failed: $_" -ForegroundColor Red
                    }
                }
            } catch {
                # Skip if we can't get command line
                continue
            }
        }
    }
}

# Stop services using saved PIDs
Write-Host "Stopping services using PID files..." -ForegroundColor Yellow
Stop-ServiceWithPidFile -ServiceName "Authentication Service" -PidFile "auth.pid"
Stop-ServiceWithPidFile -ServiceName "Transaction Service" -PidFile "transaction.pid"

# Kill any remaining Python processes related to our services
Stop-PythonProcesses

# Check if any services are still running
$authRunning = Test-Path "auth.pid"
$transRunning = Test-Path "transaction.pid"

$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdline = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdline -match "app\.main" -and ($cmdline -match "auth_service" -or $cmdline -match "transaction_service")
    } catch {
        $false
    }
}

if ($authRunning -or $transRunning -or $pythonProcesses) {
    Write-Host "`nWarning: Some services may still be running." -ForegroundColor Yellow
    
    if ($pythonProcesses) {
        Write-Host "Force killing all remaining service processes..." -ForegroundColor Yellow
        foreach ($process in $pythonProcesses) {
            try {
                Stop-Process -Id $process.Id -Force
                Write-Host "Killed process with ID $($process.Id)" -ForegroundColor Green
            } catch {
                Write-Host "Failed to kill process with ID $($process.Id): $_" -ForegroundColor Red
            }
        }
    }
    
    # Remove any remaining PID files
    if (Test-Path "auth.pid") { Remove-Item "auth.pid" -Force }
    if (Test-Path "transaction.pid") { Remove-Item "transaction.pid" -Force }
}

# Verify all services are stopped
$remainingProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
    try {
        $cmdline = (Get-WmiObject Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdline -match "app\.main" -and ($cmdline -match "auth_service" -or $cmdline -match "transaction_service")
    } catch {
        $false
    }
}

if ($remainingProcesses) {
    Write-Host "`n❌ Warning: Some service processes could not be stopped." -ForegroundColor Red
    Write-Host "   The following processes might need to be stopped manually:" -ForegroundColor Yellow
    foreach ($process in $remainingProcesses) {
        Write-Host "   - Process ID: $($process.Id)" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n✅ All services stopped!" -ForegroundColor Green
}

Write-Host "" 
Write-Host "`n✅ All services stopped!" -ForegroundColor Green 
} 