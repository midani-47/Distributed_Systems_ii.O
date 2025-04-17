#!/bin/bash

# Stop any existing services
echo "Stopping services..."
./stop_services.sh 2>/dev/null || true

# Create logs directory
mkdir -p logs

# Clear previous logs
rm -f logs/*.log

# Use absolute paths for Python interpreter
PYTHON_CMD="/opt/homebrew/opt/python@3.13/bin/python3.13"
if [ ! -f "$PYTHON_CMD" ]; then
    echo "Python interpreter not found at $PYTHON_CMD"
    PYTHON_CMD=$(which python3)
    echo "Using alternative Python: $PYTHON_CMD"
fi

echo "Starting both services..."

# Start auth service
cd auth_service && 
PYTHONPATH=. $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > ../logs/auth_service.log 2>&1 &
AUTH_PID=$!
cd ..
echo $AUTH_PID > auth_service.pid
echo "Auth service started with PID $AUTH_PID"

# Start transaction service
cd transaction_service && 
PYTHONPATH=. $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port 8081 > ../logs/transaction_service.log 2>&1 &
TRANS_PID=$!
cd ..
echo $TRANS_PID > transaction_service.pid
echo "Transaction service started with PID $TRANS_PID"

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 5

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