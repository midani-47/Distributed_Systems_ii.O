#!/bin/bash

# Stop any existing services
echo "Stopping any existing services..."
./stop_services.sh 2>/dev/null || true

# Create logs directory
mkdir -p logs

# Clear previous logs
rm -f logs/*.log

# We need to run with the correct Python version from the virtual environment
PYTHON_CMD="./venv/bin/python3"
if [ ! -f "$PYTHON_CMD" ]; then
    echo "Python executable not found at $PYTHON_CMD"
    echo "Trying alternative path..."
    PYTHON_CMD=$(which python3)
    echo "Using system Python: $PYTHON_CMD"
fi

# Run services
echo "Starting both services with $PYTHON_CMD..."

# Start auth service in the background
cd auth_service
$PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); from app.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8080)" > ../logs/auth_service.log 2>&1 &
AUTH_PID=$!
cd ..
echo $AUTH_PID > auth_service.pid
echo "Auth service started with PID $AUTH_PID"

# Start transaction service in the background
cd transaction_service
$PYTHON_CMD -c "import sys; sys.path.insert(0, '.'); from app.main import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8081)" > ../logs/transaction_service.log 2>&1 &
TRANSACTION_PID=$!
cd ..
echo $TRANSACTION_PID > transaction_service.pid
echo "Transaction service started with PID $TRANSACTION_PID"

# Wait for services to initialize
echo "Waiting for services to initialize (10 seconds)..."
sleep 10

# Print URLs
echo ""
echo "============================================="
echo "Services should now be available at:"
echo "Auth Service: http://localhost:8080/docs"
echo "Transaction Service: http://localhost:8081/docs"
echo ""
echo "To stop the services run: ./stop_services.sh"
echo "============================================="

# Wait for Ctrl+C
echo ""
echo "Press Ctrl+C to stop services..."

# Wait for interrupt
trap "echo 'Stopping services...'; ./stop_services.sh" INT
while true; do
    sleep 1
done 