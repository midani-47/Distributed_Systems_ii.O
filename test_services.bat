@echo off
:: Windows batch file wrapper to test fraud detection services
echo Testing Fraud Detection Services...

:: Check if PowerShell is available
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: PowerShell is not available on this system.
    echo Please install PowerShell to test the services.
    exit /b 1
)

:: Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "%~dp0test_services.ps1"

:: Check exit code
if %ERRORLEVEL% neq 0 (
    echo Error: Service tests failed.
    pause
    exit /b %ERRORLEVEL%
)

echo Service tests completed successfully!
exit /b 0