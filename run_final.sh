#!/bin/bash

set -e

# Stop any existing services
echo "Stopping any existing services..."
./stop_services.sh

# Function to check if a port is in use and kill the process if needed
check_port() {
    local port=$1
    if lsof -i:$port -t &>/dev/null; then
        echo "Port $port is in use. Killing the process..."
        lsof -i:$port -t | xargs kill -9 || true
        sleep 1
    fi
}

# Check if ports are in use
check_port 8080
check_port 8081

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Clear previous log files
rm -f logs/*.log

# Set cross-platform Python command
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Start Authentication Service on port 8080
echo "Starting Authentication Service on port 8080..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    cd auth_service
    AUTHENTICATION_PORT=8080 $PYTHON_CMD -m app.main > ../logs/auth_service.log 2>&1 &
    echo $! > ../auth_service.pid
    AUTH_PID=$(cat ../auth_service.pid)
    cd ..
else
    # Linux/Mac
    AUTHENTICATION_PORT=8080 $PYTHON_CMD -m app.main > logs/auth_service.log 2>&1 & 
    echo $! > auth_service.pid
    AUTH_PID=$(cat auth_service.pid)
fi
echo "Authentication Service started with PID: $AUTH_PID"

# Start Transaction Service on port 8081
echo "Starting Transaction Service on port 8081..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    cd transaction_service
    TRANSACTION_PORT=8081 $PYTHON_CMD -m app.main > ../logs/transaction_service.log 2>&1 &
    echo $! > ../transaction_service.pid
    TRANSACTION_PID=$(cat ../transaction_service.pid)
    cd ..
else
    # Linux/Mac
    TRANSACTION_PORT=8081 $PYTHON_CMD -m app.main > logs/transaction_service.log 2>&1 &
    echo $! > transaction_service.pid
    TRANSACTION_PID=$(cat transaction_service.pid)
fi
echo "Transaction Service started with PID: $TRANSACTION_PID"

# Wait for services to start
echo "Waiting for services to initialize (10 seconds)..."
sleep 10

# Test if Authentication Service is responsive
echo "Testing Authentication Service..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows - using PowerShell for HTTP request
    AUTH_RESPONSE=$(powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8080/docs' -Method 'GET' -UseBasicParsing | Select-Object -ExpandProperty StatusCode } catch { \$_.Exception.Response.StatusCode.value__ }" 2>/dev/null || echo "Error")
else
    # Linux/Mac
    AUTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/docs)
fi
echo "Authentication Service responded with HTTP code: $AUTH_RESPONSE"

if [ "$AUTH_RESPONSE" != "200" ]; then
    echo "Authentication Service failed to start properly!"
    echo "Check logs/auth_service.log for details"
    exit 1
fi

# Test if Transaction Service is responsive
echo "Testing Transaction Service..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows - using PowerShell for HTTP request
    TRANSACTION_RESPONSE=$(powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8081/docs' -Method 'GET' -UseBasicParsing | Select-Object -ExpandProperty StatusCode } catch { \$_.Exception.Response.StatusCode.value__ }" 2>/dev/null || echo "Error")
else
    # Linux/Mac
    TRANSACTION_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/docs)
fi
echo "Transaction Service responded with HTTP code: $TRANSACTION_RESPONSE"

if [ "$TRANSACTION_RESPONSE" != "200" ]; then
    echo "Transaction Service failed to start properly!"
    echo "Check logs/transaction_service.log for details"
    exit 1
fi

echo "=========================================================="
echo "Services are running!"
echo "Authentication Service: http://localhost:8080"
echo "Transaction Service: http://localhost:8081"
echo ""
echo "Example authentication:"
echo "curl -X 'POST' 'http://localhost:8080/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=admin&password=admin'"
echo ""
echo "Using the token with Transaction Service:"
echo "curl -X 'GET' 'http://localhost:8081/transactions' -H 'Authorization: Bearer YOUR_TOKEN_HERE'"
echo ""
echo "To stop the services, run: ./stop_services.sh"
echo "==========================================================" 