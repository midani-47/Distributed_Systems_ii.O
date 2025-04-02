# Financial Data System (FDS) - Authentication and Transaction Services

This project implements two main services from the FDS system:

1. **Authentication Service**: Handles user login, token generation, and validation
2. **Transaction Service**: Manages transaction data with CRUD operations

## Project Structure
```
.
├── auth_service/         # Authentication Service
│   ├── app/              # Service code
│   └── requirements.txt  # Python dependencies
├── transaction_service/  # Transaction Service  
│   ├── app/              # Service code
│   └── requirements.txt  # Python dependencies
└── logs/                 # Log files directory
```

## Authentication Service
- Supports user login with username/password
- Returns tokens with user role information
- Verifies token validity
- Uses in-memory storage

## Transaction Service
- Stores transaction data in a persistent database
- Has endpoints for CRUD operations on transactions
- Restricts access based on user roles from Authentication Service
- Logs all requests and responses

## Technical Choices
- **Framework**: FastAPI - Chosen for its simplicity, performance, and built-in OpenAPI documentation
- **Token System**: JWT (JSON Web Tokens) - For secure authentication
- **Database**: SQLite - Lightweight embedded database for persistence
- **Logging**: Python's built-in logging module with structured log formatting

## Getting Started
1. Install dependencies for each service:
   ```bash
   cd auth_service
   pip install -r requirements.txt
   cd ../transaction_service
   pip install -r requirements.txt
   ```

2. Start Authentication Service:
   ```bash
   cd auth_service
   python -m app.main
   ```

3. Start Transaction Service:
   ```bash
   cd transaction_service
   python -m app.main
   ```

4. Access API documentation:
   - Authentication Service: http://localhost:8000/docs
   - Transaction Service: http://localhost:8001/docs 