#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH=$PWD

# Stop any existing transaction service
if [ -f ../transaction_service.pid ]; then
    PID=$(cat ../transaction_service.pid)
    kill $PID 2>/dev/null || true
    rm ../transaction_service.pid
fi

# Create logs directory
mkdir -p ../logs

# Run transaction service directly
echo "Starting transaction service..."
python3 app/main.py 