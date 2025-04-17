#!/bin/bash

# Stop any existing services
./stop_services.sh

# Create logs directory
mkdir -p logs
rm -f logs/*.log

# Start auth service
cd auth_service
source ../venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 > ../logs/auth_service.log 2>&1 &
AUTH_PID=$!
echo $AUTH_PID > ../auth_service.pid
cd ..

# Start transaction service
cd transaction_service
source ../venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081 > ../logs/transaction_service.log 2>&1 &
TRANS_PID=$!
echo $TRANS_PID > ../transaction_service.pid
cd ..

# Wait for services to start
sleep 15

# Print URLs
cat << EOF
===========================================================
Services are now running:
- Auth Service: http://localhost:8080/docs
- Transaction Service: http://localhost:8081/docs

To stop the services, run: ./stop_services.sh
===========================================================
EOF

# Wait for Ctrl+C
trap "echo 'Stopping services...'; ./stop_services.sh" INT
echo "Press Ctrl+C to stop services..."
while true; do
    sleep 1
done 