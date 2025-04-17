#!/bin/bash

# Kill any existing services
pkill -f "python -m app.main" 2>/dev/null || true

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Clean any previous installations
pip uninstall -y fastapi pydantic uvicorn sqlalchemy 

# Install the latest compatible dependencies
echo "Installing dependencies compatible with Python 3.13..."
pip install --upgrade pip
pip install "fastapi<0.100.0" "uvicorn<0.22.0" "pydantic<2.0.0" sqlalchemy
pip install passlib python-multipart python-jose requests

# Create logs directory
mkdir -p logs

# Update port numbers in the code
echo "Updating port numbers in the code..."

# Update Auth Service port to 8080
sed -i '' "s/port=8000/port=8080/g" auth_service/app/main.py || true

# Update Transaction Service port to 8081 and Auth Service URL
sed -i '' "s/port=8001/port=8081/g" transaction_service/app/main.py || true
sed -i '' 's/AUTH_SERVICE_URL = "http:\/\/localhost:8000"/AUTH_SERVICE_URL = "http:\/\/localhost:8080"/g' transaction_service/app/auth.py || true

# Run auth service in the background
echo "Starting Authentication Service on port 8080..."
cd auth_service
python -m app.main > ../logs/auth_service.log 2>&1 &
AUTH_PID=$!
cd ..
echo "Authentication Service started with PID $AUTH_PID"

# Wait for auth service to start
echo "Waiting for Authentication Service to start..."
sleep 3

# Run transaction service in the background
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

# Create stop script
cat > stop_services.sh << 'EOF'
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
EOF

chmod +x stop_services.sh

# Function to check services
check_services() {
    echo "Testing Authentication Service..."
    curl -s -o /dev/null -w "Auth Service HTTP Code: %{http_code}\n" http://localhost:8080/docs || echo "Auth Service not responding"
    
    echo "Testing Transaction Service..."
    curl -s -o /dev/null -w "Transaction Service HTTP Code: %{http_code}\n" http://localhost:8081/docs || echo "Transaction Service not responding"
}

# Monitor logs
echo "Monitoring logs for errors..."
sleep 2
check_services

# Show logs if there are any issues
if ! curl -s http://localhost:8080/docs > /dev/null; then
    echo ""
    echo "Authentication Service log:"
    tail -n 20 logs/auth_service.log
fi

if ! curl -s http://localhost:8081/docs > /dev/null; then
    echo ""
    echo "Transaction Service log:"
    tail -n 20 logs/transaction_service.log
fi 