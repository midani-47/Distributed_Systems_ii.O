@echo off
echo Setting up environment...

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Check if venv exists, if not create it
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate

REM Install required packages
echo Installing required packages...
pip install -r requirements.txt

REM Ensure critical dependencies are installed
echo Verifying critical dependencies...
pip install bcrypt>=4.0.1,<5.0.0 aiohttp>=3.8.0

REM Create necessary directories
if not exist logs mkdir logs
if not exist auth_service\logs mkdir auth_service\logs
if not exist transaction_service\logs mkdir transaction_service\logs

REM Start services in separate command prompts
echo Starting Authentication Service...
start cmd /k "call venv\Scripts\activate && python -m auth_service.app.main"

REM Wait for auth service to start up
timeout /t 3 > nul

echo Starting Transaction Service...
start cmd /k "call venv\Scripts\activate && python -m transaction_service.app.main"

echo.
echo Services are starting in separate windows.
echo - Authentication Service: http://localhost:8080/docs
echo - Transaction Service: http://localhost:8081/docs
echo. 