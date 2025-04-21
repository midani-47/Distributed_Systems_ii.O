# Fraud Detection and Authentication System

This repository contains a distributed system for fraud detection with authentication.

## System Components

- **Authentication Service**: Handles user authentication and token management.
- **Transaction Service**: Manages financial transactions and fraud predictions.

## Setup and Running the System

### Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

### Option 1: Quick Setup (Recommended for Windows Users)

Run the setup script to automatically install all dependencies:

```bash
# Create and activate a virtual environment first (recommended)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Run the setup script
python setup.py
```

### Option 2: Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Linux/Mac)
# source venv/bin/activate

# Install required packages
pip install -r requirements.txt

# Ensure critical dependencies are installed properly
pip install bcrypt>=4.0.1,<5.0.0 aiohttp>=3.8.0
```

## Running the Services

### Running Directly with Python (Recommended for Windows)

Run each service in a separate terminal window:

```bash
# Terminal 1 - Auth Service
python -m auth_service.app.main

# Terminal 2 - Transaction Service
python -m transaction_service.app.main
```

### Alternative: Using the Run Script or Batch File

For Windows:
```bash
# Run the batch file
start_services.bat
```

For other platforms:
```bash
# Run both services
python run_services.py
```

The services will be available at:
- Authentication Service: http://localhost:8080/docs
- Transaction Service: http://localhost:8081/docs

## Default Users

- **Admin User**:
  - Username: admin
  - Password: admin123
  - Role: admin

- **Secretary User**:
  - Username: secretary
  - Password: secretary123
  - Role: secretary

- **Agent User**:
  - Username: agent
  - Password: agent123
  - Role: agent
  
## Testing the API

See the TEST_COMMANDS.md file for example API calls.

## Troubleshooting

Common issues and solutions:

### Windows-Specific Issues

1. **Missing bcrypt package**: If you see an error about missing bcrypt, run:
   ```
   pip install bcrypt>=4.0.1,<5.0.0
   ```

2. **SQLAlchemy errors**: Make sure you have the latest version of SQLAlchemy:
   ```
   pip install sqlalchemy>=2.0.20,<2.1.0
   ```

3. **Missing aiohttp package**: If you see an error about missing aiohttp, run:
   ```
   pip install aiohttp>=3.8.0
   ```

4. **Import errors**: Make sure you're running the services with:
   ```
   python -m auth_service.app.main
   python -m transaction_service.app.main
   ```
   
   Not with:
   ```
   python auth_service/app/main.py
   python transaction_service/app/main.py
   ```

### General Issues

1. Check the log files in the `logs` directory
   - Authentication Service: `logs/auth_service.log`
   - Transaction Service: `logs/transaction_service.log`
   
2. Ensure ports 8080 and 8081 are available:
   - On macOS/Linux: `lsof -i:8080` and `lsof -i:8081`
   - On Windows: `netstat -ano | findstr :8080` and `netstat -ano | findstr :8081`

## Important Notes

- For security purposes, never use the default admin credentials in a production environment.
- The system is configured to run locally. For production deployment, additional security measures would be required.

## Updates in Latest Version

- Added automatic fallback for bcrypt compatibility issues
- Added automatic installation of missing dependencies
- Fixed import errors for module-based execution
- Improved error handling for cross-service communication
- Added graceful fallback using requests when aiohttp is not available 