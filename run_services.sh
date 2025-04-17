#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r auth_service/requirements.txt
pip install -r transaction_service/requirements.txt

# Create logs directory
mkdir -p logs

# Run services in separate terminals
echo "Starting services..."

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && source venv/bin/activate && cd auth_service && python -m app.main"' &
    osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'\" && source venv/bin/activate && cd transaction_service && python -m app.main"' &
else
    # Linux
    gnome-terminal -- bash -c "cd \"$(pwd)\" && source venv/bin/activate && cd auth_service && python -m app.main; bash" &
    gnome-terminal -- bash -c "cd \"$(pwd)\" && source venv/bin/activate && cd transaction_service && python -m app.main; bash" &
fi

echo "Services started:"
echo "- Authentication Service: http://localhost:8000/docs"
echo "- Transaction Service: http://localhost:8001/docs" 