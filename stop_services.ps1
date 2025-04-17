# Windows PowerShell script to stop the distributed services

Write-Host "Stopping services..." -ForegroundColor Cyan

# Kill services using saved PIDs
if (Test-Path "auth_service.pid") {
    try {
        $authPid = Get-Content "auth_service.pid"
        Write-Host "Stopping Authentication Service (Job ID: $authPid)..."
        
        # Check if it's a background job
        $job = Get-Job -Id $authPid -ErrorAction SilentlyContinue
        if ($job) {
            Stop-Job -Id $authPid -ErrorAction SilentlyContinue
            Remove-Job -Id $authPid -Force -ErrorAction SilentlyContinue
        } else {
            # Try to stop as a regular process
            Stop-Process -Id $authPid -Force -ErrorAction SilentlyContinue
        }
        
        Remove-Item "auth_service.pid"
        Write-Host "Authentication Service stopped" -ForegroundColor Green
    } catch {
        Write-Host "Error stopping Authentication Service: $_" -ForegroundColor Red
    }
}

if (Test-Path "transaction_service.pid") {
    try {
        $transPid = Get-Content "transaction_service.pid"
        Write-Host "Stopping Transaction Service (Job ID: $transPid)..."
        
        # Check if it's a background job
        $job = Get-Job -Id $transPid -ErrorAction SilentlyContinue
        if ($job) {
            Stop-Job -Id $transPid -ErrorAction SilentlyContinue
            Remove-Job -Id $transPid -Force -ErrorAction SilentlyContinue
        } else {
            # Try to stop as a regular process
            Stop-Process -Id $transPid -Force -ErrorAction SilentlyContinue
        }
        
        Remove-Item "transaction_service.pid"
        Write-Host "Transaction Service stopped" -ForegroundColor Green
    } catch {
        Write-Host "Error stopping Transaction Service: $_" -ForegroundColor Red
    }
}

# Kill any remaining python processes related to our services
Write-Host "Looking for any remaining Python processes related to our services..."
$remainingProcesses = Get-Process -Name python* -ErrorAction SilentlyContinue | 
                      Where-Object { $_.CommandLine -match "app.main" }

if ($remainingProcesses) {
    Write-Host "Found remaining processes. Stopping them..." -ForegroundColor Yellow
    $remainingProcesses | ForEach-Object {
        Write-Host "Stopping process: $($_.Name) (PID: $($_.Id))"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
}

# Final verification
Start-Sleep -Seconds 2
$stillRunning = Get-Process -Name python* -ErrorAction SilentlyContinue | 
                Where-Object { $_.CommandLine -match "app.main" }

if ($stillRunning) {
    Write-Host "Some services are still running. Forcefully terminating..." -ForegroundColor Red
    $stillRunning | ForEach-Object {
        Write-Host "Force killing process: $($_.Name) (PID: $($_.Id))"
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "No remaining service processes found." -ForegroundColor Green
}

Write-Host "All services stopped!" -ForegroundColor Green 