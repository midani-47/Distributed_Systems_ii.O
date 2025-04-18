#!/bin/bash

# Universal stop script for both Windows and Unix-based systems

echo "==============================================="
echo "Fraud Detection Services - Universal Stop Script"
echo "==============================================="

# Detect operating system
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    echo "Detected Windows environment"
    
    # Check if PowerShell is available
    if command -v powershell.exe &> /dev/null; then
        echo "Stopping services using PowerShell..."
        powershell.exe -ExecutionPolicy Bypass -File "./stop_services.ps1"
    else
        echo "Error: PowerShell is not available. Please install PowerShell or run the stop script manually."
        exit 1
    fi
else
    echo "Detected Unix-based environment (Linux/macOS)"
    
    # Make sure the script is executable
    chmod +x ./stop_services.sh 2>/dev/null
    
    # Run the bash script
    ./stop_services.sh
fi 