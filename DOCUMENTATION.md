# Technical Documentation: Fraud Detection and Authentication System

## Authors
- Nevin Joseph
- Abed Midani


## Table of Contents
1. [Introduction](#introduction)
2. [System Architecture](#system-architecture)
3. [Authentication Service](#authentication-service)
4. [Transaction Service](#transaction-service)
5. [Security Implementation](#security-implementation)
6. [Logging System](#logging-system)
7. [Cross-Service Communication](#cross-service-communication)
8. [Limitations and Future Improvements](#limitations-and-future-improvements)

## Introduction

This document provides technical details about the Fraud Detection and Authentication System, a distributed application built using modern microservices architecture. The system allows financial institutions to process transactions while automatically detecting potentially fraudulent activities.

The documentation is structured to first provide a high-level overview of the system architecture, followed by detailed explanations of each service, their implementations, and how they communicate with each other. Finally, we discuss the current limitations and potential future improvements.

## System Architecture

The system follows a microservices architecture with two primary services:

1. **Authentication Service**: Responsible for user management, authentication, and token generation
2. **Transaction Service**: Handles transaction data and prediction results storage

These services are designed to operate independently, communicating via HTTP APIs, which allows for:
- Independent scaling based on load
- Isolated failure domains
- Technology flexibility
- Focused development teams

### Technology Stack

The system is built using the following technologies:

- **FastAPI**: Chosen for its high performance, automatic OpenAPI documentation, and native async support. It provides a modern, Python-based framework for building APIs with minimal boilerplate code.

- **SQLAlchemy**: Used for database interaction in the Transaction Service, providing a robust ORM layer that simplifies database operations and provides a consistent API regardless of the underlying database technology.

- **Passlib/bcrypt**: Implemented for secure password hashing in the Authentication Service. Bcrypt is specifically chosen for its adaptive nature and resistance to brute-force attacks.

- **Python-jose**: Used for JWT (JSON Web Token) generation and validation, providing a secure mechanism for cross-service authentication.

- **SQLite**: Selected as the database for the Transaction Service due to its simplicity for demonstration purposes. In a production environment, this would be replaced with a more robust database system.

- **Pydantic**: Used for data validation and settings management, ensuring type safety and providing automatic validation for incoming request data.

## Authentication Service

The Authentication Service is responsible for managing user identity and access control through token-based authentication.

### Key Components

- **User Management (users.py)**:
  - Maintains an in-memory user store
  - Provides functions to create, retrieve, and delete users
  - Handles password hashing and verification

- **Token Management (auth.py)**:
  - Generates JWT tokens upon successful authentication
  - Validates tokens for protected endpoints
  - Maintains token expiration and revocation

- **API Endpoints (main.py)**:
  - `/api/auth/login`: Authenticates users and issues tokens
  - `/api/auth/verify`: Verifies token validity
  - `/api/users`: Admin-only endpoints for user management

### Data Flow

1. A client submits credentials to the login endpoint
2. The service validates credentials against stored user data
3. If valid, a JWT token containing the user's role and a random identifier is generated
4. The token is returned to the client for use in subsequent requests

### Implementation Details

The Authentication Service uses a simple in-memory data store for user information, initialized with default users during startup. In a production environment, this would be replaced with a persistent database.

```python
# Example token generation process (simplified)
def create_access_token(username: str, role: str, expires_delta: timedelta = None):
    to_encode = {"sub": username, "role": role}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```

Password security is implemented using bcrypt hashing, which provides strong protection against various attack vectors including rainbow tables and brute force attempts.

## Transaction Service

The Transaction Service manages financial transaction data and prediction results, implementing persistent storage using SQLite and SQLAlchemy.

### Key Components

- **Database Models (database.py)**:
  - `TransactionModel`: Stores transaction metadata
  - `ResultModel`: Stores ML prediction results for transactions

- **Authentication Integration (auth.py)**:
  - Verifies tokens with the Authentication Service
  - Enforces role-based access control

- **API Endpoints (main.py)**:
  - `/api/transactions`: CRUD operations for transactions
  - `/api/transactions/{id}/results`: Operations for prediction results

### Data Flow

1. Client requests arrive with authentication tokens
2. The service validates tokens with the Authentication Service
3. If authorized, database operations are performed
4. Results are returned to the client

### Implementation Details

The Transaction Service uses SQLAlchemy as an ORM layer to interact with a SQLite database. The database schema consists of two primary tables:

1. **transactions**: Stores transaction metadata (customer, timestamp, status, vendor-ID, amount)
2. **results**: Stores prediction results (transaction ID, timestamp, is-fraudulent, confidence)

```python
# Database models (simplified)
class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.SUBMITTED)
    vendor_id = Column(String, index=True)
    amount = Column(Float)
    
    # Relationship to results
    results = relationship("ResultModel", back_populates="transaction")
```

The service implements role-based access control, allowing only users with 'admin' or 'agent' roles to access transaction data.

## Security Implementation

The system implements several security measures:

1. **Authentication**: Username/password authentication with bcrypt hashing
2. **Authorization**: JWT tokens with role information for access control
3. **Token Validation**: Verification of token validity for each request
4. **Role-Based Access Control**: Different endpoints accessible based on user role

Token verification occurs at the start of each protected endpoint call through a dependency injection pattern:

```python
# Example role-based protection (simplified)
def require_role(allowed_roles: list):
    async def role_checker(user_data: dict = Depends(verify_token)):
        role = user_data.get("role")
        if role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized. Required roles: {', '.join(allowed_roles)}"
            )
        return user_data
    return role_checker
```

## Logging System

The system implements comprehensive logging of all requests and responses, recording:

- Source IP
- Destination endpoint
- HTTP headers
- Request/response timestamps
- Request parameters
- Response status codes

Logs are written to both the console (for development convenience) and to log files:
- `auth_service.log`: Authentication Service logs
- `transaction_service.log`: Transaction Service logs

The logging implementation uses Python's standard logging module with custom formatters and handlers:

```python
# Logging setup (simplified)
def get_logger(name, log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(user)s:%(role)s]',
        '%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(f"logs/{log_file}")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
```

## Cross-Service Communication

The Transaction Service communicates with the Authentication Service for token validation:

1. When a request arrives at the Transaction Service, it extracts the token
2. The service makes an HTTP request to the Authentication Service to verify the token
3. The Authentication Service responds with token validity and user role
4. The Transaction Service proceeds with the request or returns an error based on the response

This communication is implemented using the aiohttp library to make asynchronous HTTP requests, maintaining the non-blocking nature of FastAPI:

```python
# Token verification (simplified)
async def verify_token(token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{AUTH_SERVICE_URL}/api/auth/verify",
            params={"token": token}
        ) as response:
            if response.status == 200:
                result = await response.json()
                if result.get("valid"):
                    return {"role": result.get("role")}
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
```

## Limitations and Future Improvements

The current implementation has several limitations that could be addressed in future versions:

1. **Persistence**: The Authentication Service uses in-memory storage. A production system should use a persistent database.

2. **Token Management**: The current implementation lacks comprehensive token revocation mechanisms.

3. **Service Discovery**: Service endpoints are hardcoded. A production system should implement service discovery.

4. **Scalability**: The current design doesn't address horizontal scaling concerns.

5. **Security Enhancements**: Additional security measures like rate limiting, IP filtering, and more comprehensive access control would be beneficial.

6. **ML Integration**: The current system includes data structures for ML fraud detection but doesn't implement the actual ML functionality.

Future improvements could include:

1. Adding a persistent database for the Authentication Service
2. Implementing a more robust token management system with token refresh and proper revocation
3. Adding a service discovery mechanism using tools like Consul or etcd
4. Implementing containerization with Docker and orchestration with Kubernetes
5. Adding comprehensive monitoring and alerting
6. Implementing the actual ML fraud detection system

## Conclusion

The Fraud Detection and Authentication System demonstrates a clean, modular approach to building distributed systems. By separating concerns into distinct microservices and implementing robust inter-service communication, the system provides a foundation that can be extended and improved upon for production use.

The chosen technologies (FastAPI, SQLAlchemy, JWT) provide a modern, performant stack that balances development speed with runtime efficiency. The system's architecture allows for independent scaling and maintenance of the different components, making it suitable for enterprise deployments with appropriate enhancements. 