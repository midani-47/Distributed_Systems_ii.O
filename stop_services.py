#!/usr/bin/env python3
"""
Cross-platform script to stop fraud detection services
Works on Windows, macOS, and Linux
"""

import os
import sys
import time
import signal
import psutil
import platform
from pathlib import Path

# ANSI color codes for pretty output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

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

def stop_service_by_pid_file(service_name, pid_file):
    """Stop a service using its PID file"""
    pid_file_path = SCRIPT_DIR / pid_file
    
    if not pid_file_path.exists():
        print_warning(f"{service_name} is not running (no PID file found)")
        return False
    
    try:
        with open(pid_file_path, 'r') as f:
            pid = int(f.read().strip())
        
        print_warning(f"Stopping {service_name} (PID: {pid})...")
        
        try:
            process = psutil.Process(pid)
            
            # Try a gentle termination first
            process.terminate()
            
            # Give it a moment to terminate
            try:
                process.wait(timeout=3)
                print_success(f"{service_name} stopped successfully")
            except psutil.TimeoutExpired:
                # Force kill if it doesn't terminate gracefully
                print_warning(f"{service_name} didn't terminate gracefully. Force killing...")
                process.kill()
                process.wait(timeout=3)
                print_success(f"{service_name} killed")
                
            # Remove PID file
            pid_file_path.unlink()
            return True
            
        except psutil.NoSuchProcess:
            print_warning(f"Process with PID {pid} not found. It may have already terminated.")
            pid_file_path.unlink()
            return False
            
    except Exception as e:
        print_error(f"Error stopping {service_name}: {e}")
        # Try to clean up the PID file even if we failed
        try:
            if pid_file_path.exists():
                pid_file_path.unlink()
        except:
            pass
        return False

def kill_python_service_processes():
    """Find and kill any Python processes related to our services"""
    print_warning("Checking for Python processes related to our services...")
    
    services_killed = 0
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd_line = proc.info.get('cmdline', [])
            cmd_str = " ".join(cmd_line) if cmd_line else ""
            
            # Check if this is one of our service processes
            if "app.main" in cmd_str and ("auth_service" in cmd_str or "transaction_service" in cmd_str):
                print_warning(f"Found service process: {proc.info['name']} (PID: {proc.info['pid']})")
                
                try:
                    process = psutil.Process(proc.info['pid'])
                    
                    # Kill the process
                    try:
                        # Graceful termination first
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                            print_success(f"Process terminated (PID: {proc.info['pid']})")
                        except psutil.TimeoutExpired:
                            # Force kill
                            process.kill()
                            process.wait(timeout=3)
                            print_success(f"Process killed (PID: {proc.info['pid']})")
                        
                        services_killed += 1
                    except:
                        print_error(f"Failed to kill process with PID: {proc.info['pid']}")
                except:
                    print_error(f"Failed to access process with PID: {proc.info['pid']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    if services_killed == 0:
        print_warning("No service processes found")
    else:
        print_success(f"Killed {services_killed} service processes")
    
    return services_killed > 0

def check_remaining_service_processes():
    """Check if any service processes are still running"""
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd_line = proc.info.get('cmdline', [])
            cmd_str = " ".join(cmd_line) if cmd_line else ""
            
            # Check if this is one of our service processes
            if "app.main" in cmd_str and ("auth_service" in cmd_str or "transaction_service" in cmd_str):
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return False

def main():
    print_header("Stopping Fraud Detection Services")
    
    # Stop Authentication Service
    auth_stopped = stop_service_by_pid_file("Authentication Service", "auth.pid")
    
    # Stop Transaction Service
    trans_stopped = stop_service_by_pid_file("Transaction Service", "transaction.pid")
    
    # Check for and kill any remaining service processes
    kill_python_service_processes()
    
    # Check if any services are still running
    remaining_services = check_remaining_service_processes()
    
    if remaining_services:
        print_error("\n❌ Warning: Some service processes could not be stopped.")
        print_warning("They might need to be stopped manually.")
    else:
        print()
        print_success("✅ All services stopped!")
    
    # Clean up any remaining PID files
    for pid_file in ["auth.pid", "transaction.pid"]:
        pid_path = SCRIPT_DIR / pid_file
        if pid_path.exists():
            try:
                pid_path.unlink()
                print_warning(f"Removed orphaned PID file: {pid_file}")
            except:
                pass

if __name__ == "__main__":
    main() 