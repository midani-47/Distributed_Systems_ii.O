#!/usr/bin/env python3
"""
Cross-platform script to test fraud detection services
Works on Windows, macOS, and Linux
"""

import sys
import json
import time
import platform
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import socket

# ANSI color codes for pretty output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'
    GRAY = '\033[90m'

# Service endpoints
AUTH_PORT = 8080
TRANSACTION_PORT = 8081
AUTH_URL = f"http://localhost:{AUTH_PORT}"
TRANSACTION_URL = f"http://localhost:{TRANSACTION_PORT}"

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

def test_http_endpoint(name, url, timeout=5):
    """Test if an HTTP endpoint is accessible"""
    print(f"Testing {name}... ", end="", flush=True)
    
    try:
        request = Request(url)
        response = urlopen(request, timeout=timeout)
        
        if response.status == 200:
            print_success(f"OK (Status code: {response.status})")
            return True
        else:
            print_error(f"Unexpected status code: {response.status}")
            return False
    except HTTPError as e:
        # For API endpoints, 401/403 could be expected (need authorization)
        if e.code in [401, 403] and "/docs" not in url:
            print_success(f"OK (Protected endpoint, status code: {e.code})")
            return True
        else:
            print_error(f"HTTP Error: {e.code} - {e.reason}")
            return False
    except URLError as e:
        print_error(f"Connection error: {e.reason}")
        if isinstance(e.reason, socket.timeout):
            print_warning("  The connection timed out. The service might be starting up.")
        elif "Connection refused" in str(e.reason):
            print_warning("  Connection refused. Make sure the service is running.")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def get_auth_token():
    """Get an authentication token"""
    print("\nGetting authentication token... ", end="", flush=True)
    
    auth_data = json.dumps({
        "username": "johndoe",
        "password": "password123"
    }).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        request = Request(f"{AUTH_URL}/token", data=auth_data, headers=headers, method="POST")
        response = urlopen(request, timeout=5)
        
        if response.status == 200:
            response_data = json.loads(response.read().decode('utf-8'))
            token = response_data.get("access_token")
            
            if token:
                print_success("Success! Token received.")
                return token
            else:
                print_error("No access token in response")
                return None
        else:
            print_error(f"Unexpected status code: {response.status}")
            return None
    except HTTPError as e:
        print_error(f"HTTP Error: {e.code} - {e.reason}")
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            print_warning(f"  Response: {error_body}")
        except:
            pass
        return None
    except URLError as e:
        print_error(f"Connection error: {e.reason}")
        return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return None

def test_transaction_api(token):
    """Test accessing the Transaction API with a token"""
    print("\nTesting Transaction API access... ", end="", flush=True)
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        request = Request(f"{TRANSACTION_URL}/transactions", headers=headers)
        response = urlopen(request, timeout=5)
        
        if response.status == 200:
            transactions = json.loads(response.read().decode('utf-8'))
            print_success("Success! Transaction API accessible.")
            print(f"\nFound {len(transactions)} transactions in the response.")
            return True
        else:
            print_error(f"Unexpected status code: {response.status}")
            return False
    except HTTPError as e:
        print_error(f"HTTP Error: {e.code} - {e.reason}")
        try:
            error_body = json.loads(e.read().decode('utf-8'))
            print_warning(f"  Response: {error_body}")
        except:
            pass
        return False
    except URLError as e:
        print_error(f"Connection error: {e.reason}")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    print_header("Testing Fraud Detection Services")
    
    # Test Authentication Service
    auth_docs_url = f"{AUTH_URL}/docs"
    auth_service_running = test_http_endpoint("Authentication Service", auth_docs_url)
    
    # Test Transaction Service
    transaction_docs_url = f"{TRANSACTION_URL}/docs"
    transaction_service_running = test_http_endpoint("Transaction Service", transaction_docs_url)
    
    # If both services are running, test the authentication flow
    if auth_service_running and transaction_service_running:
        print_header("Testing Authentication Flow")
        
        # Get authentication token
        token = get_auth_token()
        
        if token:
            # Test Transaction API with the token
            test_transaction_api(token)
            
            print_header("Test Complete")
            print_success("✅ All tests passed successfully!")
        else:
            print_header("Test Incomplete")
            print_error("❌ Authentication failed. Cannot test Transaction API.")
    else:
        print_header("Test Incomplete")
        print_error("❌ Cannot proceed with tests because one or more services are not running.")
        
        # Provide hints
        if not auth_service_running:
            print_warning("  - Authentication Service is not running or accessible")
            print_warning(f"    Try accessing: {auth_docs_url} in your browser")
        
        if not transaction_service_running:
            print_warning("  - Transaction Service is not running or accessible")
            print_warning(f"    Try accessing: {transaction_docs_url} in your browser")
        
        print("\nPlease start the services using:")
        print(f"{Colors.CYAN}python run_services.py{Colors.END}")

if __name__ == "__main__":
    main() 