# Technical Documentation: Fraud Detection and Authentication System

## Authors
- Abed Midani
- Nevin Joseph



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


The documentation is structured to first provide a high-level overview of the system architecture, followed by detailed explanations of each service, their implementations, and how they communicate with each other. Finally, we discuss the current limitations and potential future improvements.
This document provides technical details about a distributed application built using modern microservices architecture. 

## System Architecture

The split system follows a microservices architecture with two primary independent services:

1. **Authentication Service**: Responsible for user management, authentication, and token generation
2. **Transaction Service**: Handles transaction data and prediction results storage

These services are designed to operate independently, communicating via APIs.

### Technology Stack

The system is built using the following technologies:

- **FastAPI**: It was an interesting choice for us, because it was a new thing to explore for us. It is said to be fast comparable to others. While being easy to use and intuitive, it was still robust using Python type hints for data validation, serialization, and deserialization right out of the box, leading to fewer bugs.   
It automatically generates interactive API documentation (Swagger UI and ReDoc) based on our code. It has automatic OpenAPI documentation and native async support.

- **SQLAlchemy**: Used for database interaction in the Transaction Service, providing a robust ORM layer that simplifies database operations and provides a consistent API regardless of the underlying database technology.

- **Passlib/bcrypt**: Implemented for secure password hashing in the Authentication Service. Bcrypt is specifically chosen for its adaptive nature and resistance to brute-force attacks.

- **SQLite**: Selected as the database for the Transaction Service for simplicity for demonstration purposes. 

- **Pydantic**: Providing validation for incoming request data.

## Authentication Service

The Authentication Service is responsible for managing user identity and access control through token-based authentication.

### Key Components

- **User Management (users.py)**:
  - Maintains an in-memory user store
  - Provides functions to create, retrieve, and delete users
  - Handles password hashing and verification

- **Token Management (auth.py)**:
  - Generates custom tokens upon successful authentication
  - Validates tokens for protected endpoints
  - Handles token expiration and cleanup

- **API Endpoints (main.py)**:
  - `/api/auth/login`: Authenticates users and issues tokens
  - `/api/auth/verify`: Verifies token validity
  - `/api/users`: Admin-only endpoints for user management

### Data Flow

1. A client submits credentials to the login endpoint
2. The service validates credentials against stored user data
3. If valid, a custom token containing the user's role and a random identifier is generated
4. The token is returned to the client for use in subsequent requests

### Implementation Details

The Authentication Service uses a simple in-memory data store for user information, initialized with default users during startup. In a production environment, this would be replaced with a persistent database.

```python
# Example token generation process (from auth_service/app/auth.py)
def create_access_token(username: str, role: str) -> str:
    # generating random token component for security
    random_part = base64.b64encode(os.urandom(16)).decode('utf-8')
    
    # embedding role information in token structure
    token = f"{random_part}|{role}"
    
    # calculating token expiration time
    expiry = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    # storing token in memory database with metadata
    tokens_db[token] = {
        "username": username,
        "role": role,
        "expiry": expiry
    }
    
    logger.info(f"Token created for: {username}")
    return token
```

## Transaction Service

The Transaction Service manages financial transaction data and prediction results, implementing mechanisms for caching using SQLite and SQLAlchemy.

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
# Database models (from transaction_service/app/database.py)
class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.SUBMITTED)
    vendor_id = Column(String, index=True)
    amount = Column(Float)
    
    # establishing relationship with results table for ORM
    results = relationship("ResultModel", back_populates="transaction")
```

The service implements role-based access control, allowing only users with 'admin' or 'agent' roles to access transaction data.

## Security Implementation

The system implements several security measures:

1. **Authentication**: Username/password authentication with bcrypt hashing
2. **Authorization**: Custom token system with role information for access control
3. **Token Validation**: Verification of token validity for each request
4. **Role-Based Access Control**: Different endpoints accessible based on user role

Token verification occurs at the start of each protected endpoint call through a dependency injection pattern:

```python
# Example role-based protection (from transaction_service/app/auth.py)
def require_role(allowed_roles: list):
    """
    Check if the user has one of the allowed roles
    """
    async def role_checker(user_data: dict = Depends(verify_token)):
        role = user_data.get("role")
        
        # enforcing role-based access control
        if role not in allowed_roles:
            logger.warning(f"Authorization failed: Role {role} not in {allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized. Required roles: {', '.join(allowed_roles)}"
            )
        
        logger.info(f"Authorization successful for role: {role}")
        return user_data
    
    return role_checker
```

## Logging System

Our system implements comprehensive request/response logging across both services, capturing all interactions between clients and services as well as inter-service communication.

### Logging Architecture

Each service has its own independent logging system with the following components:

1. **Logger Configuration**:
   - Each service initializes its own logger (auth_service.logger and transaction_service.logger)
   - Loggers are configured with both console and file handlers
   - Log files are stored in the `logs` directory with service-specific files

2. **HTTP Middleware**:
   - Both services implement FastAPI middleware to intercept all HTTP requests and responses
   - The middleware extracts detailed information before and after request processing
   - Custom filtering ensures sensitive information (passwords, tokens) is masked or truncated

3. **Log Storage**:
   - Console output for development convenience
   - File-based persistent logs for auditing and troubleshooting
   - Structured JSON format for machine readability

### Log Content

Every logged request contains the following fields:

- **timestamp**: ISO-8601 formatted date and time
- **source**: Client IP address and port (or service name for inter-service calls)
- **destination**: Service name, port, and endpoint path
- **method**: HTTP method (GET, POST, PUT, DELETE)
- **path**: Full request path including query parameters
- **headers**: All HTTP headers (with sensitive values redacted)
- **query_params**: URL query parameters (when present)
- **body**: Request body

Response logs capture:

- **timestamp**: ISO-8601 formatted date and time
- **request_id**: Same UUID as the corresponding request
- **statusCode**: HTTP status code
- **headers**: Response headers
- **body**: Response body (may be truncated for large responses)

Example implementation in the Authentication Service:

```python
# Middleware for request logging (from auth_service/app/main.py)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # logging request metadata without body content
    log_request_info(request)
    
    # processing the request through the middleware chain
    response = await call_next(request)
    
    # endpoints handle their own response logging using LoggingJSONResponse
    return response
```

### Inter-Service Logging

The Transaction Service logs all communication with the Authentication Service:

```python
# Log inter-service communication (from transaction_service/app/auth.py)
# logging inter-service communication for debugging
print(f"\n[SERVICE-COMM] Transaction -> Auth Service | Verify Token")
print(f"  Token: {token[:10]}...")

# logging inter-service response
print(f"[SERVICE-COMM] Auth Service -> Transaction | Response: {status_code}")
```

### Log File Structure

The system creates and maintains the following log directory structure:
```
/logs
  ├── auth_service.log     # Authentication Service logs
  └── transaction_service.log  # Transaction Service logs
```

Additional service-specific logs are stored in their respective service directories:
```
/auth_service/logs/
/transaction_service/logs/
```

### Log Analysis

The logs can be analyzed using standard text processing tools or imported into log analysis platforms. The JSON formatting facilitates structured querying and filtering.

For production environments, we recommend implementing a more robust logging solution using tools like ELK Stack (Elasticsearch, Logstash, Kibana) or Graylog for centralized log collection and analysis.

## Cross-Service Communication

The Transaction Service communicates with the Authentication Service for token validation:

1. When a request arrives at the Transaction Service, it extracts the token
2. The service makes an HTTP request to the Authentication Service to verify the token
3. The Authentication Service responds with token validity and user role
4. The Transaction Service proceeds with the request or returns an error based on the response

This communication is implemented using the aiohttp library to make asynchronous HTTP requests, maintaining the non-blocking nature of FastAPI:

```python
# Token verification (from transaction_service/app/auth.py)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify token with the Authentication Service
    """
    token = credentials.credentials
    logger.info(f"Verifying token: {token[:10] if len(token) > 10 else token}...")
    
    # handling multiple Bearer prefixes that can occur with certain clients
    while token.startswith("Bearer "):
        token = token[7:]
    
    logger.info(f"Clean token after removing Bearer prefix: {token[:10] if len(token) > 10 else token}")
    
    # logging inter-service communication for debugging
    print(f"\n[SERVICE-COMM] Transaction -> Auth Service | Verify Token")
    print(f"  Token: {token[:10]}...")
    
    try:
        # preparing request to authentication service
        logger.info(f"Sending verification request to: {AUTH_SERVICE_URL}/verify-token")
        
        # using async HTTP client for non-blocking requests
        async with aiohttp.ClientSession() as session:
            # attempting verification with primary endpoint
            async with session.get(
                f"{AUTH_SERVICE_URL}/verify-token",
                params={"token": token},
                timeout=10  # preventing infinite wait on network issues
            ) as response:
                # ...rest of implementation
```

## Limitations and Future Improvements

The current implementation has several limitations that could be addressed in future versions:

1. **Persistence**: The Authentication Service uses in-memory storage. A production system should use a persistent database.

2. **Token Security**: The current implementation uses a simple custom token system. A production environment should use a more robust solution like JWT with signature verification.

3. **Service Discovery**: Service endpoints are hardcoded. A production system should implement service discovery.

4. **Scalability**: The current design doesn't address horizontal scaling concerns.

5. **Security Enhancements**: Additional security measures like rate limiting, IP filtering, and more comprehensive access control would be beneficial.

6. **ML Integration**: The current system includes data structures for ML fraud detection but doesn't implement the actual ML functionality.

Future improvements could include:

1. Adding a persistent database for the Authentication Service
2. Implementing a proper JWT token system with signature verification 
3. Adding a service discovery mechanism using tools like Consul or etcd
4. Implementing containerization with Docker and orchestration with Kubernetes
5. Adding comprehensive monitoring and alerting
6. Implementing the actual ML fraud detection system

## Conclusion

The Fraud Detection and Authentication System demonstrates a clean, modular approach to building distributed systems. By separating concerns into distinct microservices and implementing robust inter-service communication, the system provides a foundation that can be extended and improved upon for production use.

The chosen technologies (FastAPI, SQLAlchemy, custom token authentication) provide a modern, performant stack that balances development speed with runtime efficiency. The system's architecture allows for independent scaling and maintenance of the different components, making it suitable for enterprise deployments with appropriate enhancements. 
