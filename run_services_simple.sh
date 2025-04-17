#!/bin/bash

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
pip install fastapi uvicorn pydantic sqlalchemy
pip install passlib python-multipart python-jose requests

# Create logs directory
mkdir -p logs

echo "Starting services in separate terminals..."

# For macOS, use AppleScript to open new terminal windows
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Get the absolute path of the current directory
    CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Start auth service
    osascript -e "tell application \"Terminal\" to do script \"cd \\\"$CURRENT_DIR\\\" && source venv/bin/activate && cd auth_service && python -m app.main\""
    
    # Start transaction service
    osascript -e "tell application \"Terminal\" to do script \"cd \\\"$CURRENT_DIR\\\" && source venv/bin/activate && cd transaction_service && python -m app.main\""
else
    # For Linux
    echo "For Linux, please run each service manually in separate terminals:"
    echo "Terminal 1: cd auth_service && python -m app.main"
    echo "Terminal 2: cd transaction_service && python -m app.main"
fi

echo ""
echo "Once services are started, you can access them at:"
echo "- Authentication Service: http://localhost:8000/docs"
echo "- Transaction Service: http://localhost:8001/docs" 