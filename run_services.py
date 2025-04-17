import os
import sys
import subprocess
import time
import signal
import platform
import socket
import webbrowser
from pathlib import Path
import atexit

# Print some debug information
print(f"Current working directory: {os.getcwd()}")
print(f"Python executable: {sys.executable}")
print(f"Platform: {platform.system()}")

# Function to check if a port is in use
def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

# Function to stop services using PIDs
def stop_services():
    print("\nStopping services...")
    # Kill services using saved PIDs
    if os.path.exists("auth_service.pid"):
        try:
            with open("auth_service.pid", "r") as f:
                pid = int(f.read().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
            os.remove("auth_service.pid")
        except:
            pass
        print("Authentication Service stopped")

    if os.path.exists("transaction_service.pid"):
        try:
            with open("transaction_service.pid", "r") as f:
                pid = int(f.read().strip())
                try:
                    os.kill(pid, signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
            os.remove("transaction_service.pid")
        except:
            pass
        print("Transaction Service stopped")

    # Force cleanup in case processes are still running
    if platform.system() == "Windows":
        subprocess.run("taskkill /f /im python.exe /fi \"WINDOWTITLE eq app.main*\"", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.run("pkill -f \"python -m app.main\" || true", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    print("All services stopped!")

# Register stop_services to run on exit
atexit.register(stop_services)

# Stop any existing services
stop_services()

# Check and clear ports
auth_port = 8080
transaction_port = 8081

for port in [auth_port, transaction_port]:
    if is_port_in_use(port):
        print(f"Port {port} is in use. Attempting to free it...")
        if platform.system() == "Windows":
            subprocess.run(f"FOR /F \"tokens=5\" %a in ('netstat -ano ^| findstr :{port}') do taskkill /PID %a /F", shell=True)
        else:
            subprocess.run(f"lsof -i:{port} -t | xargs kill -9 || true", shell=True)
        time.sleep(1)

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Clear previous log files
for log_file in Path("logs").glob("*.log"):
    try:
        log_file.unlink()
    except:
        pass

print("Starting services...")

# Determine Python executable to use
python_cmd = sys.executable
print(f"Using Python executable: {python_cmd}")

# Start Authentication Service
print(f"Starting Authentication Service on port {auth_port}...")
auth_env = os.environ.copy()
auth_env["AUTHENTICATION_PORT"] = str(auth_port)
auth_env["PYTHONPATH"] = os.getcwd() + "/auth_service"

try:
    os.chdir("auth_service")
    auth_process = subprocess.Popen(
        [python_cmd, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(auth_port)],
        env=auth_env,
        stdout=open(os.path.join("..", "logs", "auth_service.log"), "w"),
        stderr=subprocess.STDOUT
    )
    os.chdir("..")
    with open("auth_service.pid", "w") as f:
        f.write(str(auth_process.pid))
    print(f"Authentication Service started with PID: {auth_process.pid}")
except Exception as e:
    print(f"Error starting Authentication Service: {e}")
    sys.exit(1)

# Start Transaction Service
print(f"Starting Transaction Service on port {transaction_port}...")
transaction_env = os.environ.copy()
transaction_env["TRANSACTION_PORT"] = str(transaction_port)
transaction_env["PYTHONPATH"] = os.getcwd() + "/transaction_service"

try:
    os.chdir("transaction_service")
    transaction_process = subprocess.Popen(
        [python_cmd, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(transaction_port)],
        env=transaction_env,
        stdout=open(os.path.join("..", "logs", "transaction_service.log"), "w"),
        stderr=subprocess.STDOUT
    )
    os.chdir("..")
    with open("transaction_service.pid", "w") as f:
        f.write(str(transaction_process.pid))
    print(f"Transaction Service started with PID: {transaction_process.pid}")
except Exception as e:
    print(f"Error starting Transaction Service: {e}")
    auth_process.terminate()
    sys.exit(1)

# Wait for services to start
print("Waiting for services to initialize (10 seconds)...")
time.sleep(10)

# Test if services are responsive
print("\nTesting services:")
auth_url = f"http://localhost:{auth_port}/docs"
transaction_url = f"http://localhost:{transaction_port}/docs"

def check_service(url, name):
    try:
        import urllib.request
        print(f"Attempting to connect to {url}")
        response = urllib.request.urlopen(url, timeout=5)
        status = response.status
        print(f"Response status: {status}")
        if status == 200:
            print(f"✅ {name} is running: {url}")
            return True
        else:
            print(f"❌ {name} returned status code {status}")
            return False
    except Exception as e:
        print(f"❌ {name} is not responding: {e}")
        return False

auth_ok = check_service(auth_url, "Authentication Service")
transaction_ok = check_service(transaction_url, "Transaction Service")

if not auth_ok or not transaction_ok:
    print("\nSome services failed to start. Checking logs for details:")
    if not auth_ok:
        print("Authentication Service logs:")
        try:
            with open(os.path.join("logs", "auth_service.log"), "r") as f:
                log_content = f.read()
                print(log_content[-2000:] if len(log_content) > 2000 else log_content)  # Show last 2000 chars only
        except Exception as e:
            print(f"Could not read log file: {e}")
    
    if not transaction_ok:
        print("Transaction Service logs:")
        try:
            with open(os.path.join("logs", "transaction_service.log"), "r") as f:
                log_content = f.read()
                print(log_content[-2000:] if len(log_content) > 2000 else log_content)  # Show last 2000 chars only
        except Exception as e:
            print(f"Could not read log file: {e}")
    
    print("\nPress Ctrl+C to stop services and exit")

print("\n" + "="*60)
print("Services are running!")
print(f"Authentication Service: {auth_url}")
print(f"Transaction Service: {transaction_url}")
print("")
print("Example authentication:")
print(f"curl -X 'POST' '{auth_url.replace('/docs', '/token')}' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=admin&password=admin'")
print("")
print("To stop the services, press Ctrl+C")
print("="*60)

# Attempt to open services in browser
try:
    print("Attempting to open browser windows...")
    webbrowser.open(auth_url)
    time.sleep(1)
    webbrowser.open(transaction_url)
except Exception as e:
    print(f"Failed to open browser: {e}")

# Keep the script running and handle Ctrl+C gracefully
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nKeyboard interrupt received, stopping services...")
    stop_services()
    sys.exit(0) 