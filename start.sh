#!/bin/bash

# Define variables for port configuration
AUTH_PORT=${AUTHENTICATION_PORT:-8080}
TRANS_PORT=${TRANSACTION_PORT:-8081}

echo "==============================================="
echo "Starting Fraud Detection Services (Unix/macOS)"
echo "==============================================="

# Stop any existing services
if [ -f ./stop_services.sh ]; then
    echo "Stopping any existing services..."
    ./stop_services.sh
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    local process_info=$(lsof -i :$port -sTCP:LISTEN -t 2>/dev/null)
    if [ -n "$process_info" ]; then
        echo "Warning: Port $port is already in use!"
        echo "Process ID using port $port: $process_info"
        read -p "Do you want to kill this process? (y/n) " confirm
        if [[ $confirm == [yY] ]]; then
            kill $process_info 2>/dev/null || kill -9 $process_info 2>/dev/null
            echo "Process killed."
            sleep 1
        else
            echo "Please choose another port."
            exit 1
        fi
    fi
}

# Check if ports are in use
check_port $AUTH_PORT
check_port $TRANS_PORT

# Create logs directory
echo "Setting up logs directory..."
mkdir -p logs
rm -f logs/*.log

# Determine virtual environment path and activation
VENV_ACTIVATE=""
if [ -f "venv/bin/activate" ]; then
    VENV_ACTIVATE="venv/bin/activate"
elif [ -f ".venv/bin/activate" ]; then
    VENV_ACTIVATE=".venv/bin/activate"
fi

if [ -z "$VENV_ACTIVATE" ]; then
    echo "Error: Virtual environment not found. Please create it first."
    exit 1
fi

# Start auth service
echo "Starting Authentication Service on port $AUTH_PORT..."
cd auth_service
source ../$VENV_ACTIVATE
export AUTHENTICATION_PORT=$AUTH_PORT
python -m uvicorn app.main:app --host 0.0.0.0 --port $AUTH_PORT > ../logs/auth_service.log 2>&1 &
AUTH_PID=$!
echo $AUTH_PID > ../auth_service.pid
cd ..

# Wait a moment to ensure the service starts
sleep 5

# Start transaction service
echo "Starting Transaction Service on port $TRANS_PORT..."
cd transaction_service
source ../$VENV_ACTIVATE
export TRANSACTION_PORT=$TRANS_PORT
python -m uvicorn app.main:app --host 0.0.0.0 --port $TRANS_PORT > ../logs/transaction_service.log 2>&1 &
TRANS_PID=$!
echo $TRANS_PID > ../transaction_service.pid
cd ..

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Print URLs
cat << EOF
===========================================================
Services are now running:
- Auth Service: http://localhost:$AUTH_PORT/docs
- Transaction Service: http://localhost:$TRANS_PORT/docs

To stop the services, run: ./stop_services.sh
===========================================================
EOF

# Wait for Ctrl+C
trap "echo 'Stopping services...'; ./stop_services.sh" INT
echo "Press Ctrl+C to stop services..."
while true; do
    sleep 1
done 