# Fraud Detection and Authentication System

This repository contains a distributed system for fraud detection with authentication.

## System Components

- **Authentication Service**: Handles user authentication and token management.
- **Transaction Service**: Manages financial transactions and fraud predictions.

## Setup and Running the System

### Prerequisites

- Python 3.8 or higher
- Virtual environment (venv)

### Setup Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Activate virtual environment (Windows)
# venv\Scripts\activate
```

### Install Required Packages

```bash
pip install -r requirements.txt
```

## Running the Services

To run both services, use the provided start script:

```bash
# Make the script executable if needed
chmod +x start.sh

# Run the services
./start.sh
```

The services will be available at:
- Authentication Service: http://localhost:8080/docs
- Transaction Service: http://localhost:8081/docs

To stop the services, press Ctrl+C in the terminal window or run:
```bash
./stop_services.sh
```

## API Usage Examples

### Authentication

1. Get authentication token:

```bash
curl -X 'POST' 'http://localhost:8080/token' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin&password=admin'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

2. Use the token with Transaction Service:

```bash
curl -X 'GET' 'http://localhost:8081/transactions' \
  -H 'Authorization: Bearer YOUR_TOKEN_HERE'
```

## Default Users

- **Admin User**:
  - Username: admin
  - Password: admin123
  - Role: admin

- **Agent User**:
  - Username: agent
  - Password: agent123
  - Role: agent
  
## Troubleshooting

If you encounter issues:

1. Check the log files in the `logs` directory
   - Authentication Service: `logs/auth_service.log`
   - Transaction Service: `logs/transaction_service.log`
   
2. Ensure ports 8080 and 8081 are available:
   - On macOS/Linux: `lsof -i:8080` and `lsof -i:8081`
   - On Windows: `netstat -ano | findstr :8080` and `netstat -ano | findstr :8081`

3. Make sure Python dependencies are installed correctly:
   ```bash
   pip list | grep fastapi
   pip list | grep uvicorn
   ```

## Important Notes

- For security purposes, never use the default admin credentials in a production environment.
- The system is configured to run locally. For production deployment, additional security measures would be required. 