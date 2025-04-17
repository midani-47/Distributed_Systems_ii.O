# Distributed Authentication and Transaction Services

This project implements a distributed system with two microservices:
- **Authentication Service**: Manages user authentication and token generation
- **Transaction Service**: Processes financial transactions with authorization

## Platform Compatibility

The implementation is compatible with:
- Windows
- macOS
- Linux

## Requirements

- Python 3.7+
- A virtual environment

## Getting Started

### 1. Clone and Setup

```bash
# Clone the repository (if applicable)
git clone <repository_url>
cd <project_directory>

# Create and activate a virtual environment
# For Windows:
python -m venv venv
.\venv\Scripts\activate  # Windows PowerShell
# OR
venv\Scripts\activate.bat  # Windows Command Prompt

# For macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Running the Services

#### On Windows:

Use the PowerShell scripts for Windows environments:

```powershell
# Start all services
.\run_services.ps1

# Test if services are working properly
.\test_services.ps1

# Stop all services
.\stop_services.ps1
```

#### On macOS/Linux:

Use the Bash scripts for Unix-based environments:

```bash
# Make scripts executable
chmod +x run_final.sh stop_services.sh test_services.sh

# Start all services
./run_final.sh

# Test if services are working properly
./test_services.sh

# Stop all services
./stop_services.sh
```

### 3. API Documentation

Once running, you can access the API documentation at:
- Authentication Service: http://localhost:8080/docs
- Transaction Service: http://localhost:8081/docs

## Service Architecture

### Authentication Service (Port 8080)

- **Login**: `POST /token` - OAuth2 compliant token endpoint
- **Token verification**: `GET /api/auth/verify` - Verifies token validity
- **User management**: Admin endpoints for user CRUD operations

### Transaction Service (Port 8081)

- **List transactions**: `GET /transactions` - Returns list of transactions
- **Create transaction**: `POST /api/transactions` - Create a new transaction
- **Update transaction**: `PUT /api/transactions/{id}` - Update transaction status

## Troubleshooting

### Port conflicts

The services require ports 8080 and 8081. If these ports are in use:
- The startup scripts will attempt to free these ports
- You can manually stop processes using these ports

### Logging

Log files are stored in the `logs` directory:
- `auth_service.log` - Authentication service logs
- `transaction_service.log` - Transaction service logs

### Common Issues

1. **Virtual Environment**: Ensure you have activated the virtual environment
2. **Port Already in Use**: 
   - Windows: Use `netstat -ano | findstr :8080` to find the PID using port 8080
   - Unix: Use `lsof -i:8080` to identify processes using port 8080
3. **Permission Denied**: Ensure scripts have execution permissions on Unix systems

## Default Users

The Authentication Service comes with pre-configured users:
- `admin` / `admin` (Admin role)
- `agent` / `agent123` (Agent role)
- `user` / `user123` (User role) 