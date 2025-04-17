#!/usr/bin/env python3
import sys
import os
import subprocess
import time
import signal
import webbrowser
import atexit

print("Using direct execution method for services")
print(f"Current directory: {os.getcwd()}")
print(f"Using Python: {sys.executable}")

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Function to stop services
def stop_services():
    print("Stopping services...")
    # Try to kill by PID files
    for pid_file in ["auth_service.pid", "transaction_service.pid"]:
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                    try:
                        os.kill(pid, signal.SIGTERM)
                        print(f"Stopped service with PID {pid}")
                    except:
                        pass
                os.remove(pid_file)
            except:
                pass
    
    # Kill any remaining processes
    try:
        if os.name == 'nt':  # Windows
            subprocess.run("taskkill /f /im python.exe /fi \"WINDOWTITLE eq app.main*\"", shell=True)
        else:  # Unix/Mac
            subprocess.run("pkill -f \"python.*app.main\" || true", shell=True)
    except:
        pass
    
    print("All services stopped!")

# Register cleanup function
atexit.register(stop_services)

# Stop any running services first
stop_services()

# Auth service arguments
auth_port = 8080
auth_log = os.path.abspath(os.path.join("logs", "auth_service.log"))

# Transaction service arguments
transaction_port = 8081
transaction_log = os.path.abspath(os.path.join("logs", "transaction_service.log"))

# First run auth service
print(f"Starting Auth Service on port {auth_port}...")
os.chdir("auth_service")
auth_env = os.environ.copy()
auth_env["AUTHENTICATION_PORT"] = str(auth_port)

try:
    # Run directly with Python, not as a module
    auth_script = os.path.abspath(os.path.join("app", "main.py"))
    with open(auth_log, "w") as log_file:
        auth_process = subprocess.Popen(
            [sys.executable, auth_script],
            env=auth_env,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
    
    # Go back to parent directory and save PID
    os.chdir("..")
    with open("auth_service.pid", "w") as f:
        f.write(str(auth_process.pid))
    
    print(f"Auth Service started with PID {auth_process.pid}")

except Exception as e:
    print(f"Error starting Auth Service: {e}")
    os.chdir("..")
    sys.exit(1)

# Now run transaction service
print(f"Starting Transaction Service on port {transaction_port}...")
os.chdir("transaction_service")
transaction_env = os.environ.copy()
transaction_env["TRANSACTION_PORT"] = str(transaction_port)

try:
    # Run directly with Python, not as a module
    transaction_script = os.path.abspath(os.path.join("app", "main.py"))
    with open(transaction_log, "w") as log_file:
        transaction_process = subprocess.Popen(
            [sys.executable, transaction_script],
            env=transaction_env,
            stdout=log_file,
            stderr=subprocess.STDOUT
        )
    
    # Go back to parent directory and save PID
    os.chdir("..")
    with open("transaction_service.pid", "w") as f:
        f.write(str(transaction_process.pid))
    
    print(f"Transaction Service started with PID {transaction_process.pid}")

except Exception as e:
    print(f"Error starting Transaction Service: {e}")
    os.chdir("..")
    auth_process.terminate()
    sys.exit(1)

# Wait for services to initialize
print("Waiting for services to initialize (10 seconds)...")
time.sleep(10)

# URLs to open in browser
auth_url = f"http://localhost:{auth_port}/docs"
transaction_url = f"http://localhost:{transaction_port}/docs"

print("=" * 60)
print("Services should now be running!")
print(f"Authentication Service: {auth_url}")
print(f"Transaction Service: {transaction_url}")
print()
print("Opening browser windows...")

# Try to open browser tabs
try:
    webbrowser.open(auth_url)
    time.sleep(1)
    webbrowser.open(transaction_url)
except Exception as e:
    print(f"Couldn't open browser: {e}")

print()
print("To authenticate:")
print(f"curl -X 'POST' 'http://localhost:{auth_port}/token' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=admin&password=admin'")
print("=" * 60)

print("\nPress Ctrl+C to stop services...")

# Keep running until interrupted
try:
    while True:
        time.sleep(1)
        # Check if processes are still running
        if auth_process.poll() is not None:
            print(f"Auth service terminated with exit code {auth_process.returncode}")
            print("Check logs/auth_service.log for details")
            break
        
        if transaction_process.poll() is not None:
            print(f"Transaction service terminated with exit code {transaction_process.returncode}")
            print("Check logs/transaction_service.log for details")
            break
        
except KeyboardInterrupt:
    print("\nStopping services...")

# Cleanup will happen automatically via atexit 