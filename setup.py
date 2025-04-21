import sys
import subprocess
import os

def setup_environment():
    """Set up the environment for running the application."""
    print("Setting up environment...")
    
    # Install required packages
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("Required packages installed successfully.")
        
        # Make sure bcrypt and aiohttp are properly installed
        print("Verifying critical dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt>=4.0.1,<5.0.0", "aiohttp>=3.8.0"])
        print("Critical dependencies verified.")
    except Exception as e:
        print(f"Failed to install packages: {e}")
        return False
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Create necessary directories
    for service_dir in ["auth_service/logs", "transaction_service/logs"]:
        os.makedirs(service_dir, exist_ok=True)
    
    print("\nSetup completed successfully!")
    print("\nTo run the auth service, use: python -m auth_service.app.main")
    print("To run the transaction service, use: python -m transaction_service.app.main")
    
    return True

if __name__ == "__main__":
    setup_environment() 