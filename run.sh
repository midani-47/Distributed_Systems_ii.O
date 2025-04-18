#!/bin/bash

# Universal startup script for both Windows and Unix-based systems

# Default port configuration
AUTH_PORT=${AUTHENTICATION_PORT:-8080}
TRANS_PORT=${TRANSACTION_PORT:-8081}

echo "==============================================="
echo "Fraud Detection Services - Universal Launcher"
echo "==============================================="

# Detect operating system
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows environment"
    
    # Check if PowerShell is available
    if command -v powershell.exe &> /dev/null; then
        echo "Starting services using PowerShell..."
        powershell.exe -ExecutionPolicy Bypass -File "./run_services.ps1" -auth_port $AUTH_PORT -transaction_port $TRANS_PORT
    else
        echo "Error: PowerShell is not available. Please install PowerShell or run the script manually."
        exit 1
    fi
else
    echo "Detected Unix-based environment (Linux/macOS)"
    
    # Make sure the script is executable
    chmod +x ./start.sh 2>/dev/null
    
    # Run the bash script with environment variables
    export AUTHENTICATION_PORT=$AUTH_PORT
    export TRANSACTION_PORT=$TRANS_PORT
    ./start.sh
fi 