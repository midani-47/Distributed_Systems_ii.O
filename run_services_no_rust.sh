#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install simplified requirements that don't need Rust
echo "Installing dependencies that don't require Rust..."
pip install fastapi==0.95.2 uvicorn==0.22.0 pydantic==1.10.8 passlib==1.7.4 python-multipart==0.0.6 python-jose==3.3.0
pip install sqlalchemy==2.0.15 requests==2.31.0

# Create logs directory
mkdir -p logs

# Prepare to run services
echo "Starting services..."

# Function to run a service
run_service() {
    cd "$1"
    echo "Starting $1 service on port $2..."
    python -m app.main &
    SERVICE_PID=$!
    echo "$SERVICE_PID" > "../$1.pid"
    cd ..
    echo "$1 service started with PID $SERVICE_PID"
}

# Run services
run_service "auth_service" 8000
run_service "transaction_service" 8001

echo ""
echo "Services started:"
echo "- Authentication Service: http://localhost:8000/docs"
echo "- Transaction Service: http://localhost:8001/docs"
echo ""
echo "To stop services, run: ./stop_services.sh"

# Create a script to stop services
cat > stop_services.sh << 'EOF'
#!/bin/bash
echo "Stopping services..."
if [ -f "auth_service.pid" ]; then
    PID=$(cat auth_service.pid)
    kill $PID 2>/dev/null || true
    rm auth_service.pid
    echo "Auth service stopped"
fi
if [ -f "transaction_service.pid" ]; then
    PID=$(cat transaction_service.pid)
    kill $PID 2>/dev/null || true
    rm transaction_service.pid
    echo "Transaction service stopped"
fi
echo "All services stopped"
EOF

chmod +x stop_services.sh 