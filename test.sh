#!/bin/bash

# Universal test script for both Windows and Unix-based systems

# Default configuration
AUTH_PORT=${AUTHENTICATION_PORT:-8080}
TRANS_PORT=${TRANSACTION_PORT:-8081}
USERNAME=${TEST_USERNAME:-admin}
PASSWORD=${TEST_PASSWORD:-admin}

echo "==============================================="
echo "Fraud Detection Services - Universal Test Script"
echo "==============================================="

# Detect operating system
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows environment"
    
    # Check if PowerShell is available
    if command -v powershell.exe &> /dev/null; then
        echo "Running tests using PowerShell..."
        powershell.exe -ExecutionPolicy Bypass -File "./test_services.ps1" -auth_port $AUTH_PORT -transaction_port $TRANS_PORT -username $USERNAME -password $PASSWORD
    else
        echo "Error: PowerShell is not available. Please install PowerShell or run the test script manually."
        exit 1
    fi
else
    echo "Detected Unix-based environment (Linux/macOS)"
    
    # Make sure the script is executable
    chmod +x ./test_services.sh 2>/dev/null
    
    # Run the bash script with environment variables
    export AUTHENTICATION_PORT=$AUTH_PORT
    export TRANSACTION_PORT=$TRANS_PORT
    export TEST_USERNAME=$USERNAME
    export TEST_PASSWORD=$PASSWORD
    ./test_services.sh
fi 