# Windows PowerShell script to stop services

Write-Host "Stopping services..."

# Kill services using saved PIDs (though these may not be accurate in Windows)
if (Test-Path -Path ".\auth_service.pid") {
    $auth_pid = Get-Content -Path ".\auth_service.pid"
    try {
        Stop-Process -Id $auth_pid -ErrorAction SilentlyContinue
    } catch {
        # Process may not exist anymore
    }
    Remove-Item -Path ".\auth_service.pid" -Force
    Write-Host "Authentication Service stopped"
}

if (Test-Path -Path ".\transaction_service.pid") {
    $transaction_pid = Get-Content -Path ".\transaction_service.pid"
    try {
        Stop-Process -Id $transaction_pid -ErrorAction SilentlyContinue
    } catch {
        # Process may not exist anymore
    }
    Remove-Item -Path ".\transaction_service.pid" -Force
    Write-Host "Transaction Service stopped"
}

# Find and kill any remaining Python processes related to our services
$pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*app.main*" -or $_.CommandLine -like "*uvicorn*" } 

if ($pythonProcesses) {
    foreach ($process in $pythonProcesses) {
        try {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped Python process with ID: $($process.Id)"
        } catch {
            # Process may not exist anymore
        }
    }
}

# Additional check for Python processes using our ports
$portUsage = netstat -ano | Select-String "LISTENING" | Select-String ":(8080|8081) "
if ($portUsage) {
    $portUsage | ForEach-Object {
        $processId = ($_ -split '\s+')[-1] -as [int]
        if ($processId) {
            try {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Write-Host "Stopped process with ID: $processId that was using our ports"
            } catch {
                # Process may not exist anymore 
            }
        }
    }
}

# Wait a moment to ensure processes have time to stop
Start-Sleep -Seconds 2

# Check if any processes are still using our ports
$remainingPortUsage = netstat -ano | Select-String "LISTENING" | Select-String ":(8080|8081) "
if ($remainingPortUsage) {
    Write-Host "Warning: Some processes are still using our ports:"
    $remainingPortUsage | ForEach-Object {
        Write-Host $_
    }
    
    $confirmKill = Read-Host "Do you want to forcefully kill these processes? (y/n)"
    if ($confirmKill.ToLower() -eq 'y') {
        $remainingPortUsage | ForEach-Object {
            $processId = ($_ -split '\s+')[-1] -as [int]
            if ($processId) {
                try {
                    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                    Write-Host "Forcefully stopped process with ID: $processId"
                } catch {
                    # Process may not exist anymore
                }
            }
        }
    }
}

Write-Host "All services stopped!" 