#!/usr/bin/env python3
"""
Simplified script to run fraud detection services
Works on Windows, macOS, and Linux without additional dependencies
"""

import os
import sys
import time
import subprocess
import socket
from pathlib import Path

# Service ports
AUTH_PORT = 8080
TRANSACTION_PORT = 8081

# Get script directory
SCRIPT_DIR = Path(__file__).resolve().parent

def print_colored(message, color_code):
    """Print colored text if supported"""
    print(f"\033[{color_code}m{message}\033[0m")

def print_success(message):
    """Print success message in green"""
    print_colored(message, "92")

def print_warning(message):
    """Print warning message in yellow"""
    print_colored(message, "93")

def print_error(message):
    """Print error message in red"""
    print_colored(message, "91")

def print_header(message):
    """Print header message in cyan"""
    print_colored(f"\n=== {message} ===\n", "96")

def is_port_in_use(port):
    """Check if port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def ensure_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = SCRIPT_DIR / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir()
        print_success(f"Created logs directory at {logs_dir}")
    return logs_dir

def start_service(name, working_dir, pid_file, command):
    """Start a service and save its PID"""
    print_warning(f"Starting {name}...")
    
    service_dir = SCRIPT_DIR / working_dir
    logs_dir = ensure_logs_directory()
    log_file = logs_dir / f"{name.lower().replace(' ', '_')}.log"
    
    # Set environment variables
    env = os.environ.copy()
    env["AUTH_SERVICE_PORT"] = str(AUTH_PORT)
    env["TRANSACTION_SERVICE_PORT"] = str(TRANSACTION_PORT)
    
    # Start process and redirect output to log file
    with open(log_file, 'w') as f:
        try:
            # Use Popen to start the process
            process = subprocess.Popen(
                command,
                cwd=service_dir,
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                shell=True
            )
            
            # Save PID to file
            pid_file_path = SCRIPT_DIR / pid_file
            with open(pid_file_path, 'w') as pf:
                pf.write(str(process.pid))
            
            # Wait a bit for service to start
            time.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                print_success(f"{name} started successfully (PID: {process.pid})")
                return True, process.pid
            else:
                print_error(f"{name} failed to start")
                return False, None
                
        except Exception as e:
            print_error(f"Error starting {name}: {e}")
            return False, None

def main():
    print_header("Starting Fraud Detection Services")
    
    # Check for port conflicts
    ports_to_check = [AUTH_PORT, TRANSACTION_PORT]
    for port in ports_to_check:
        if is_port_in_use(port):
            print_error(f"Port {port} is already in use. Please free up this port and try again.")
            sys.exit(1)
    
    # Set environment variables
    os.environ["AUTH_SERVICE_PORT"] = str(AUTH_PORT)
    os.environ["TRANSACTION_SERVICE_PORT"] = str(TRANSACTION_PORT)
    
    # Start Authentication Service
    auth_cmd = f"{sys.executable} -m app.main"
    auth_success, auth_pid = start_service(
        "Authentication Service", 
        "auth_service", 
        "auth.pid", 
        auth_cmd
    )
    
    # Start Transaction Service
    trans_cmd = f"{sys.executable} -m app.main"
    trans_success, trans_pid = start_service(
        "Transaction Service", 
        "transaction_service", 
        "transaction.pid", 
        trans_cmd
    )
    
    # Display info about running services
    print_header("Service Status")
    
    logs_dir = ensure_logs_directory()
    auth_log = logs_dir / "authentication_service.log"
    trans_log = logs_dir / "transaction_service.log"
    
    if auth_success:
        print_success(f"✅ Authentication Service: Running on http://localhost:{AUTH_PORT}")
        print(f"   - API Documentation: http://localhost:{AUTH_PORT}/docs")
        print(f"   - Log file: {auth_log}")
    else:
        print_error("❌ Authentication Service: Failed to start")
    
    if trans_success:
        print_success(f"✅ Transaction Service: Running on http://localhost:{TRANSACTION_PORT}")
        print(f"   - API Documentation: http://localhost:{TRANSACTION_PORT}/docs")
        print(f"   - Log file: {trans_log}")
    else:
        print_error("❌ Transaction Service: Failed to start")
    
    if auth_success and trans_success:
        print()
        print_success("✅ All services started successfully!")
        print("   - To test the services: python simple_test_services.py")
        print("   - To stop the services: python simple_stop_services.py")
    else:
        print()
        print_error("❌ Some services failed to start. Check the logs for details.")

if __name__ == "__main__":
    main() 