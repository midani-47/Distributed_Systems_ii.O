# Financial Data System (FDS) - Authentication and Transaction Services

This project implements two main microservices from the FDS system:

1. **Authentication Service**: Handles user login and token validation
2. **Transaction Service**: Manages transaction data with CRUD operations and fraud prediction results

## Architecture & Ports

```
+-----------------+        +-----------------+
|  Authentication |        |   Transaction   |
|     Service     |        |     Service     |
|   (port 8000)   |◄------>|   (port 8001)   |
+-----------------+        +-----------------+
         ▲                         ▲
         |                         |
         ▼                         ▼
     +-------+               +-----------+
     |  RAM  |               |   SQLite  |
     | Store |               |  Database |
     +-------+               +-----------+
```

## Tech Stack Choices

Both services are implemented using:

- **Language**: Python 3.8+
- **Framework**: FastAPI
  - Chosen for its speed (based on Starlette and Pydantic)
  - Built-in OpenAPI documentation (Swagger UI)
  - Type hints and automatic validation
  - Asynchronous support
  - Lightweight and easy to use

- **Database**:
  - Auth Service: In-memory storage for users and tokens
  - Transaction Service: SQLite for persistent storage

## API Design & Documentation

### Authentication Service
- `POST /api/auth/login` - User login and token generation
- `GET /api/auth/verify` - Token verification
- `POST /api/users` - Create new users (admin only)
- `DELETE /api/users/{username}` - Delete users (admin only)

### Transaction Service
- `POST /api/transactions` - Create a new transaction
- `GET /api/transactions` - List all transactions
- `GET /api/transactions/{id}` - Get a specific transaction
- `PUT /api/transactions/{id}` - Update transaction status
- `POST /api/transactions/{id}/results` - Add fraud prediction result
- `GET /api/transactions/{id}/results` - Get fraud prediction results

## Getting Started

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation and Running

1. Clone the repository
2. Run the provided script to start both services:
   ```bash
   ./run_services.sh
   ```

This will:
- Create a virtual environment
- Install all dependencies
- Start both services in separate terminals

You can also run each service manually:

```bash
# Auth Service
cd auth_service
python -m app.main

# Transaction Service
cd transaction_service
python -m app.main
```

## Authentication Workflow

1. Login using pre-configured users:
   ```
   admin/admin123 (role: admin)
   secretary/secretary123 (role: secretary)
   agent/agent123 (role: agent)
   ```

2. Use the returned token in the Authorization header:
   ```
   Authorization: Bearer <token>
   ```

## Comprehensive Logging

All services implement detailed structured logging for both requests and responses, including:
- Timestamp
- Source (client IP) 
- Destination (service name + port)
- Headers
- Request body/params
- Response status code
- Response body

Logs are stored in the `logs/` directory and also output to the console.

## Testing the Services

You can use the Swagger UI documentation to test the APIs:
- Authentication Service: http://localhost:8000/docs
- Transaction Service: http://localhost:8001/docs

### Example Usage

1. Login with admin credentials:
   ```bash
   curl -X 'POST' \
     'http://localhost:8000/api/auth/login' \
     -H 'Content-Type: application/json' \
     -d '{
     "username": "admin",
     "password": "admin123"
   }'
   ```

2. Create a transaction:
   ```bash
   curl -X 'POST' \
     'http://localhost:8001/api/transactions' \
     -H 'Authorization: Bearer <token>' \
     -H 'Content-Type: application/json' \
     -d '{
     "customer": "John Doe",
     "vendor_id": "V12345",
     "amount": 1000.50
   }'
   ```

3. Add a fraud prediction result:
   ```bash
   curl -X 'POST' \
     'http://localhost:8001/api/transactions/1/results' \
     -H 'Authorization: Bearer <token>' \
     -H 'Content-Type: application/json' \
     -d '{
     "is_fraudulent": false,
     "confidence": 0.95
   }'
   ``` 