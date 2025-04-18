@echo off
:: Windows batch file wrapper to stop fraud detection services
echo Stopping Fraud Detection Services...

:: Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: PowerShell is not available on this system.
    echo Please install PowerShell to stop the services.
    exit /b 1
)

:: Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0stop_services.ps1"

:: Check exit code
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to stop services.
    pause
    exit /b %ERRORLEVEL%
)

echo Services stopped successfully!
exit /b 0 