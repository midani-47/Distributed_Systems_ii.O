#!/bin/bash

# Stop any existing services
echo "Stopping services..."
./stop_services.sh 2>/dev/null || true

# Create logs directory
mkdir -p logs

# Clear previous logs
rm -f logs/*.log

echo "Starting both services..."

# Ensure we're in a virtual environment with all dependencies
if [ -f "./venv/bin/activate" ]; then
    source ./venv/bin/activate
    echo "Activated virtual environment"
else
    echo "Virtual environment not found at ./venv/bin/activate"
    exit 1
fi

# Check for required dependencies
pip list | grep -q "fastapi" || { echo "FastAPI not installed in active environment"; exit 1; }
pip list | grep -q "uvicorn" || { echo "Uvicorn not installed in active environment"; exit 1; }

# Use Python from virtual environment
PYTHON_CMD=$(which python)
echo "Using Python: $PYTHON_CMD"

# Start auth service
echo "Starting authentication service on port 8080..."
cd auth_service 
echo "Directory: $(pwd)"
echo "PYTHONPATH=. $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > ../logs/auth_service.log 2>&1"
PYTHONPATH=. $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > ../logs/auth_service.log 2>&1 &
AUTH_PID=$!
cd ..
echo $AUTH_PID > auth_service.pid
echo "Auth service started with PID $AUTH_PID"

# Start transaction service
echo "Starting transaction service on port 8081..."
cd transaction_service
echo "Directory: $(pwd)"
echo "PYTHONPATH=. $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8081 > ../logs/transaction_service.log 2>&1"
PYTHONPATH=. $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8081 > ../logs/transaction_service.log 2>&1 &
TRANS_PID=$!
cd ..
echo $TRANS_PID > transaction_service.pid
echo "Transaction service started with PID $TRANS_PID"

# Wait for services to initialize (longer timeout to ensure both services start)
echo "Waiting for services to initialize (15 seconds)..."
sleep 15

# Check if services are running
echo "Checking if services are running..."
curl -s -o /dev/null -w "Auth Service: %{http_code}\n" http://localhost:8080/docs || echo "Auth Service: Failed"
curl -s -o /dev/null -w "Transaction Service: %{http_code}\n" http://localhost:8081/docs || echo "Transaction Service: Failed"

# Print URLs
echo ""
echo "=============================================
Services should now be available at:
Auth Service: http://localhost:8080/docs
Transaction Service: http://localhost:8081/docs
To stop the services run: ./stop_services.sh
============================================="

echo "Press Ctrl+C to stop services..."
trap "echo 'Stopping services...'; ./stop_services.sh" INT
while true; do
    sleep 1
done 