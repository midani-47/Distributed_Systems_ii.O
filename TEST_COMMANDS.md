# Testing the Authentication and Transaction Services

This document provides curl commands to test both services once they are running. You'll need to use two terminal windows, one for each service.

## Prerequisites

Before running the tests, you need to:

1. Install Python 3.8+ and pip
2. Install the Rust compiler (required for pydantic): https://rustup.rs/
3. Run the services in two separate terminals:

Terminal 1 (Auth Service):
```bash
cd auth_service
python -m app.main
```

Terminal 2 (Transaction Service):
```bash
cd transaction_service
python -m app.main
```

## Test Authentication Service

### 1. Login as an admin user

```bash
curl -X 'POST' \
  'http://localhost:8000/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "admin",
  "password": "admin123"
}'
```

Expected response:
```json
{
  "token": "base64_random_string|admin"
}
```

### 2. Login as a secretary user

```bash
curl -X 'POST' \
  'http://localhost:8000/api/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{
  "username": "secretary",
  "password": "secretary123"
}'
```

### 3. Verify a token (replace with your token)

```bash
curl -X 'GET' \
  'http://localhost:8000/api/auth/verify?token=YOUR_TOKEN'
```

Expected response:
```json
{
  "valid": true,
  "role": "admin"
}
```

## Test Transaction Service

### 1. Create a transaction (with admin token)

```bash
curl -X 'POST' \
  'http://localhost:8001/api/transactions' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "customer": "John Doe",
  "vendor_id": "VENDOR123",
  "amount": 1000.50
}'
```

Expected response:
```json
{
  "id": 1,
  "customer": "John Doe",
  "vendor_id": "VENDOR123",
  "amount": 1000.50,
  "timestamp": "2023-04-02T12:34:56.789012",
  "status": "submitted"
}
```

### 2. List all transactions

```bash
curl -X 'GET' \
  'http://localhost:8001/api/transactions' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### 3. Add a prediction result for transaction 1

```bash
curl -X 'POST' \
  'http://localhost:8001/api/transactions/1/results' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "is_fraudulent": false,
  "confidence": 0.95
}'
```

### 4. Get transaction details including fraud prediction

```bash
curl -X 'GET' \
  'http://localhost:8001/api/transactions/1' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

Expected response:
```json
{
  "id": 1,
  "customer": "John Doe",
  "vendor_id": "VENDOR123",
  "amount": 1000.50,
  "timestamp": "2023-04-02T12:34:56.789012",
  "status": "submitted",
  "is_fraudulent": false,
  "confidence": 0.95
}
```

### 5. Update transaction status

```bash
curl -X 'PUT' \
  'http://localhost:8001/api/transactions/1?status=accepted' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### 6. Get prediction results for transaction 1

```bash
curl -X 'GET' \
  'http://localhost:8001/api/transactions/1/results' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

## Testing Authorization Restrictions

### 1. Try to create a transaction using secretary token (should fail)

```bash
curl -X 'POST' \
  'http://localhost:8001/api/transactions' \
  -H 'Authorization: Bearer SECRETARY_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
  "customer": "John Doe",
  "vendor_id": "VENDOR123",
  "amount": 500
}'
```

Expected response:
```json
{
  "detail": "Access denied: role secretary not allowed"
}
```

### 2. Try to create a transaction without token (should fail)

```bash
curl -X 'POST' \
  'http://localhost:8001/api/transactions' \
  -H 'Content-Type: application/json' \
  -d '{
  "customer": "John Doe",
  "vendor_id": "VENDOR123",
  "amount": 500
}'
```

Expected response:
```json
{
  "detail": "Not authenticated"
}
``` 