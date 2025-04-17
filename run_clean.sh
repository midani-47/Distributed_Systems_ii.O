#!/bin/bash

# Kill any existing services
echo "Stopping any existing services..."
pkill -f "python -m app.main" 2>/dev/null || true
./stop_services.sh 2>/dev/null || true

# Activate virtual environment
source venv/bin/activate

# Create logs directory
mkdir -p logs

# Clear previous log files
echo "Clearing previous logs..."
rm -f logs/auth_service.log logs/transaction_service.log

# Start services
echo "Starting services..."

# Run auth service (port 8080)
echo "Starting Authentication Service on port 8080..."
cd auth_service
python -m app.main > ../logs/auth_service.log 2>&1 &
AUTH_PID=$!
cd ..
echo "Authentication Service started with PID $AUTH_PID"

# Wait for auth service to start
echo "Waiting for Authentication Service to start..."
sleep 5

# Run transaction service (port 8081)
echo "Starting Transaction Service on port 8081..."
cd transaction_service
python -m app.main > ../logs/transaction_service.log 2>&1 &
TRANSACTION_PID=$!
cd ..
echo "Transaction Service started with PID $TRANSACTION_PID"

# Save PIDs for later cleanup
echo "$AUTH_PID" > auth_service.pid
echo "$TRANSACTION_PID" > transaction_service.pid

echo ""
echo "Services started:"
echo "- Authentication Service: http://localhost:8080/docs"
echo "- Transaction Service: http://localhost:8081/docs"
echo ""
echo "Debug logs available at:"
echo "- Authentication Service: logs/auth_service.log"
echo "- Transaction Service: logs/transaction_service.log"
echo ""
echo "To stop the services, run: ./stop_services.sh"

# Test if services are responding
sleep 2
echo ""
echo "Testing services:"
echo "- Authentication Service: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/docs || echo "Not responding")"
echo "- Transaction Service: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/docs || echo "Not responding")"
echo ""

# Check logs if services aren't responding
if ! curl -s http://localhost:8080/docs > /dev/null; then
    echo "Authentication Service log:"
    tail -n 20 logs/auth_service.log
fi

if ! curl -s http://localhost:8081/docs > /dev/null; then
    echo "Transaction Service log:"
    tail -n 20 logs/transaction_service.log
fi 