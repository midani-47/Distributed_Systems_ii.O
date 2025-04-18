#!/usr/bin/env python3
"""
Cross-platform script to run fraud detection services
Works on Windows, macOS, and Linux
"""

import os
import sys
import time
import signal
import subprocess
import socket
import platform
import psutil
from pathlib import Path

# ANSI color codes for pretty output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'
    GRAY = '\033[90m'

# Ports for services
AUTH_PORT = 8080
TRANSACTION_PORT = 8081

# Get the script directory
SCRIPT_DIR = Path(__file__).resolve().parent

def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}=== {message} ==={Colors.END}\n")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}{message}{Colors.END}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}{message}{Colors.END}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}{message}{Colors.END}")

def is_port_in_use(port):
    """Check if a port is in use by creating a test socket"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def kill_process_on_port(port):
    """Kill the process using the specified port"""
    print_warning(f"Port {port} is already in use.")
    
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            # Check for connections
            for conn in proc.connections(kind='inet'):
                if conn.laddr.port == port:
                    print_warning(f"Found process using port {port}: {proc.name()} (PID: {proc.pid})")
                    print_warning(f"Stopping process...")
                    try:
                        proc.terminate()
                        proc.wait(timeout=3)
                        print_success("Process terminated")
                        return True
                    except:
                        try:
                            proc.kill()
                            print_success("Process killed")
                            return True
                        except:
                            print_error(f"Failed to kill process on port {port}")
                            return False
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    print_warning(f"No process found using port {port}")
    return False

def ensure_logs_directory():
    """Create the logs directory if it doesn't exist"""
    logs_dir = SCRIPT_DIR / "logs"
    if not logs_dir.exists():
        logs_dir.mkdir()
        print_success(f"Created logs directory at {logs_dir}")
    return logs_dir

def activate_virtual_environment():
    """Set up the Python path and virtual environment"""
    # Determine the correct path to the virtual environment
    venv_paths = [
        SCRIPT_DIR / "venv",
        SCRIPT_DIR / ".venv",
        Path("venv"),
        Path(".venv")
    ]
    
    venv_path = None
    for path in venv_paths:
        if path.exists():
            venv_path = path
            break
    
    if not venv_path:
        print_warning("No virtual environment found. Will try to proceed without it.")
        return
    
    print_warning("Activating virtual environment...")
    
    # Set Python path
    os.environ["PYTHONPATH"] = str(SCRIPT_DIR)
    
    # On Windows, we need to use the Scripts directory
    if platform.system() == "Windows":
        os.environ["PATH"] = f"{venv_path / 'Scripts'}{os.pathsep}{os.environ['PATH']}"
    else:
        os.environ["PATH"] = f"{venv_path / 'bin'}{os.pathsep}{os.environ['PATH']}"
    
    print_success("Virtual environment activated")

def start_service(name, working_dir, pid_file, cmd):
    """Start a service and return its process"""
    print_warning(f"Starting {name}...")
    
    service_dir = SCRIPT_DIR / working_dir
    logs_dir = ensure_logs_directory()
    log_file = logs_dir / f"{name.lower().replace(' ', '_')}.log"
    
    # Set environment variables
    env = os.environ.copy()
    env["AUTH_SERVICE_PORT"] = str(AUTH_PORT)
    env["TRANSACTION_SERVICE_PORT"] = str(TRANSACTION_PORT)
    
    # Create startup command based on platform
    if platform.system() == "Windows":
        # Use pythonw on Windows to avoid command window
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = 0  # Hide the console window
        
        # Start the process with output redirected to log file
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                cwd=service_dir,
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                startupinfo=startup_info,
                shell=True
            )
    else:
        # On Unix systems, start the process and redirect output to log file
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd,
                cwd=service_dir,
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                shell=True,
                preexec_fn=os.setsid  # Create a new process group on Unix
            )
    
    # Save PID to file
    pid_file_path = SCRIPT_DIR / pid_file
    with open(pid_file_path, 'w') as f:
        f.write(str(process.pid))
    
    # Wait a moment for the service to start
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is None:
        print_success(f"{name} started successfully (PID: {process.pid})")
        return True, process.pid
    else:
        print_error(f"{name} failed to start")
        return False, None

def check_service_health(name, url, max_retries=5):
    """Check if a service is healthy by accessing its health endpoint"""
    import urllib.request
    
    print_warning(f"Checking if {name} is responding...")
    
    for i in range(max_retries):
        try:
            response = urllib.request.urlopen(url, timeout=2)
            if response.status == 200:
                print_success(f"{name} is ready!")
                return True
        except Exception as e:
            print_warning(f"Waiting for {name}... (Attempt {i+1}/{max_retries})")
            time.sleep(2)
    
    print_error(f"{name} is not responding after {max_retries} attempts")
    return False

def main():
    print_header("Starting Fraud Detection Services")
    
    # First stop any running services to avoid conflicts
    stop_script = SCRIPT_DIR / "stop_services.py"
    if stop_script.exists():
        print_warning("Stopping any running services...")
        subprocess.run([sys.executable, stop_script])
    
    # Check for port conflicts
    ports_to_check = [AUTH_PORT, TRANSACTION_PORT]
    for port in ports_to_check:
        if is_port_in_use(port):
            success = kill_process_on_port(port)
            if not success:
                print_error(f"Failed to free port {port}. Please close the application using this port manually.")
                sys.exit(1)
    
    # Activate virtual environment
    activate_virtual_environment()
    
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
        print(f"{Colors.GRAY}   - API Documentation: http://localhost:{AUTH_PORT}/docs{Colors.END}")
        print(f"{Colors.GRAY}   - Log file: {auth_log}{Colors.END}")
    else:
        print_error("❌ Authentication Service: Failed to start")
    
    if trans_success:
        print_success(f"✅ Transaction Service: Running on http://localhost:{TRANSACTION_PORT}")
        print(f"{Colors.GRAY}   - API Documentation: http://localhost:{TRANSACTION_PORT}/docs{Colors.END}")
        print(f"{Colors.GRAY}   - Log file: {trans_log}{Colors.END}")
    else:
        print_error("❌ Transaction Service: Failed to start")
    
    if auth_success and trans_success:
        print()
        print_success("✅ All services started successfully!")
        print(f"{Colors.CYAN}   - To test the services: python test_services.py{Colors.END}")
        print(f"{Colors.CYAN}   - To stop the services: python stop_services.py{Colors.END}")
    else:
        print()
        print_error("❌ Some services failed to start. Check the logs for details.")

if __name__ == "__main__":
    main() 