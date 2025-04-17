#!/bin/bash
echo "Stopping services..."
if [ -f "auth_service.pid" ]; then
    PID=$(cat auth_service.pid)
    kill $PID 2>/dev/null || true
    rm auth_service.pid
    echo "Authentication Service stopped"
fi
if [ -f "transaction_service.pid" ]; then
    PID=$(cat transaction_service.pid)
    kill $PID 2>/dev/null || true
    rm transaction_service.pid
    echo "Transaction Service stopped"
fi
echo "All services stopped"
