#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH=$PWD

# Stop any existing auth service
if [ -f ../auth_service.pid ]; then
    PID=$(cat ../auth_service.pid)
    kill $PID 2>/dev/null || true
    rm ../auth_service.pid
fi

# Create logs directory
mkdir -p ../logs

# Run auth service directly
echo "Starting auth service..."
python3 app/main.py 