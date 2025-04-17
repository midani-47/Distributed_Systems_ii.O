"""
Run services directly from Python
Run this script directly in the IDE to start both services
"""

import os
import sys
import subprocess
import time
import signal
import webbrowser
import atexit

print("Starting services directly from Python...")

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Clear any existing log files
for log_file in ["auth_service.log", "transaction_service.log"]:
    log_path = os.path.join("logs", log_file)
    if os.path.exists(log_path):
        try:
            os.remove(log_path)
        except:
            pass

# Function to stop services
def stop_services():
    print("\nStopping services...")
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

# Register cleanup
atexit.register(stop_services)

# First, stop any running services
stop_services()

# Get Python executable (this should be the one from the virtual environment)
python_exe = sys.executable
print(f"Using Python executable: {python_exe}")

# Start the authentication service
print("Starting authentication service...")
os.makedirs("logs", exist_ok=True)

auth_cmd = [
    python_exe,
    "-c",
    """
import sys
import os
sys.path.insert(0, os.path.abspath('auth_service'))
from app.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8080)
"""
]

auth_log = open(os.path.join("logs", "auth_service.log"), "w")
auth_process = subprocess.Popen(auth_cmd, stdout=auth_log, stderr=subprocess.STDOUT)
with open("auth_service.pid", "w") as f:
    f.write(str(auth_process.pid))
print(f"Authentication service started with PID {auth_process.pid}")

# Start the transaction service
print("Starting transaction service...")
trans_cmd = [
    python_exe,
    "-c",
    """
import sys
import os
sys.path.insert(0, os.path.abspath('transaction_service'))
from app.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8081)
"""
]

trans_log = open(os.path.join("logs", "transaction_service.log"), "w")
trans_process = subprocess.Popen(trans_cmd, stdout=trans_log, stderr=subprocess.STDOUT)
with open("transaction_service.pid", "w") as f:
    f.write(str(trans_process.pid))
print(f"Transaction service started with PID {trans_process.pid}")

# Wait for services to initialize
print("Waiting for services to initialize (10 seconds)...")
time.sleep(10)

# Print service URLs
auth_url = "http://localhost:8080/docs"
trans_url = "http://localhost:8081/docs"

print("\n" + "=" * 60)
print("Services should now be running at:")
print(f"- Authentication Service: {auth_url}")
print(f"- Transaction Service: {trans_url}")
print("=" * 60)

# Try to open browser windows
try:
    webbrowser.open(auth_url)
    time.sleep(1)
    webbrowser.open(trans_url)
except:
    print("Could not open browser windows automatically")

# Keep the script running until interrupted
print("\nPress Ctrl+C to stop the services and exit...")
try:
    while True:
        # Check if the processes are still running
        auth_status = auth_process.poll()
        trans_status = trans_process.poll()
        
        if auth_status is not None:
            print(f"Authentication service has exited with code {auth_status}")
            print("Check logs/auth_service.log for details")
            break
            
        if trans_status is not None:
            print(f"Transaction service has exited with code {trans_status}")
            print("Check logs/transaction_service.log for details")
            break
            
        time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down services...") 