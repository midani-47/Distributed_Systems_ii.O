@echo off
:: Windows batch file wrapper to run fraud detection services
echo Starting Fraud Detection Services...

:: Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: PowerShell is not available on this system.
    echo Please install PowerShell to run the services.
    exit /b 1
)

:: Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0run_services.ps1"

:: Check exit code
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to start services.
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0 