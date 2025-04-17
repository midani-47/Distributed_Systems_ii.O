#!/bin/bash

echo "Stopping services..."

# Kill services using saved PIDs
if [ -f auth_service.pid ]; then
    AUTH_PID=$(cat auth_service.pid)
    kill $AUTH_PID 2>/dev/null || true
    rm auth_service.pid
    echo "Authentication Service stopped"
fi

if [ -f transaction_service.pid ]; then
    TRANSACTION_PID=$(cat transaction_service.pid)
    kill $TRANSACTION_PID 2>/dev/null || true
    rm transaction_service.pid
    echo "Transaction Service stopped"
fi

# Kill any remaining python processes related to our services
pkill -f "python -m app.main" 2>/dev/null || true

# Check if processes are still running
sleep 2
if pgrep -f "python -m app.main" > /dev/null; then
    echo "Some services are still running. Forcefully terminating..."
    pkill -9 -f "python -m app.main" 2>/dev/null || true
fi

echo "All services stopped!"
