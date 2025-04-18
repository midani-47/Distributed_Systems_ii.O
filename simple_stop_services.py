#!/usr/bin/env python3
"""
Simplified script to stop fraud detection services
Works on Windows, macOS, and Linux without additional dependencies
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

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
            # First try sending SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            print_success(f"{service_name} stopped successfully")
            
            # Remove PID file
            pid_file_path.unlink()
            return True
            
        except ProcessLookupError:
            print_warning(f"Process with PID {pid} not found. It may have already terminated.")
            pid_file_path.unlink()
            return False
            
        except Exception as e:
            print_error(f"Error sending SIGTERM to {service_name}: {e}")
            
            # Try SIGKILL as last resort
            try:
                os.kill(pid, signal.SIGKILL)
                print_success(f"{service_name} force killed")
                pid_file_path.unlink()
                return True
            except Exception as e2:
                print_error(f"Error force killing {service_name}: {e2}")
            
    except Exception as e:
        print_error(f"Error reading PID file for {service_name}: {e}")
    
    # Try to clean up the PID file even if we failed
    try:
        if pid_file_path.exists():
            pid_file_path.unlink()
    except:
        pass
    
    return False

def kill_service_processes_by_name():
    """Use platform-specific commands to find and kill service processes"""
    print_warning("Checking for remaining service processes...")
    
    try:
        # Use basic subprocess calls to find and kill processes
        if sys.platform == "win32":
            # Windows - use tasklist and taskkill
            cmd = 'tasklist /FI "IMAGENAME eq python.exe" /FO CSV'
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            
            for line in output.splitlines()[1:]:  # Skip header
                if 'app.main' in line and ('auth_service' in line or 'transaction_service' in line):
                    parts = line.split(',')
                    if len(parts) >= 2:
                        pid = parts[1].strip('"')
                        subprocess.call(f'taskkill /F /PID {pid}', shell=True)
                        print_success(f"Killed process with PID {pid}")
        else:
            # Unix - use ps and kill
            cmd = "ps -ef | grep 'app.main\\|auth_service\\|transaction_service' | grep -v grep"
            try:
                output = subprocess.check_output(cmd, shell=True).decode('utf-8')
                
                for line in output.splitlines():
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        try:
                            os.kill(int(pid), signal.SIGKILL)
                            print_success(f"Killed process with PID {pid}")
                        except:
                            pass
            except subprocess.CalledProcessError:
                # No matching processes found
                pass
    except Exception as e:
        print_error(f"Error trying to find and kill service processes: {e}")

def main():
    print_header("Stopping Fraud Detection Services")
    
    # Stop Authentication Service
    auth_stopped = stop_service_by_pid_file("Authentication Service", "auth.pid")
    
    # Stop Transaction Service
    trans_stopped = stop_service_by_pid_file("Transaction Service", "transaction.pid")
    
    # Try to kill any remaining processes
    kill_service_processes_by_name()
    
    # Clean up any remaining PID files
    for pid_file in ["auth.pid", "transaction.pid"]:
        pid_path = SCRIPT_DIR / pid_file
        if pid_path.exists():
            try:
                pid_path.unlink()
                print_warning(f"Removed orphaned PID file: {pid_file}")
            except:
                pass
    
    print()
    print_success("✅ All services stopped!")

if __name__ == "__main__":
    main() 