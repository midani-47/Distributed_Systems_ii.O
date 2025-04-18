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

```powershell
curl -Method POST `
  -Uri "http://localhost:8080/api/auth/login" `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{ "username": "admin", "password": "admin123" }'
```

Expected response:
```json
{
StatusCode        : 200
StatusDescription : OK
Content           : {"access_token":"Vb/d9V2YczXhrrrFznUEwQ==|admin","token_type":"bearer"}
...
}
```

### 2. Login as a secretary user

```powershell
curl -Method POST `
  -Uri "http://localhost:8080/api/auth/login" `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{ "username": "secretary", "password": "secretary123" }'
```

### 3. Verify a token (replace with your token)

```powershell
curl -Method GET `
  -Uri "http://localhost:8080/api/auth/verify?token=YOUR_TOKEN"
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

```powershell
curl -Method POST `
  -Uri "http://localhost:8081/api/transactions" `
  -Headers @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Content-Type"  = "application/json"
  } `
  -Body '{ "customer": "John Doe", "vendor_id": "VENDOR123", "amount": 1000.50 }'
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

```powershell
curl -Method GET `
  -Uri "http://localhost:8081/api/transactions" `
  -Headers @{ "Authorization" = "Bearer YOUR_TOKEN" }
```

### 3. Add a prediction result for transaction 1

```powershell
curl -Method POST `
  -Uri "http://localhost:8081/api/transactions/1/results" `
  -Headers @{
    "Authorization" = "Bearer YOUR_TOKEN"
    "Content-Type"  = "application/json"
  } `
  -Body '{ "is_fraudulent": false, "confidence": 0.95 }'
```

### 4. Get transaction details including fraud prediction

```powershell
curl -Method GET `
  -Uri "http://localhost:8081/api/transactions/1" `
  -Headers @{ "Authorization" = "Bearer YOUR_TOKEN" }
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

```powershell
curl -Method PUT `
  -Uri "http://localhost:8081/api/transactions/1?status=accepted" `
  -Headers @{ "Authorization" = "Bearer YOUR_TOKEN" }
```

### 6. Get prediction results for transaction 1

```powershell
curl -Method GET `
  -Uri "http://localhost:8081/api/transactions/1/results" `
  -Headers @{ "Authorization" = "Bearer YOUR_TOKEN" }
```
note 1 is the ID, change number to desired input

## Testing Authorization Restrictions

### 1. Try to create a transaction using secretary token (should fail)

```powershell
curl -Method POST `
  -Uri "http://localhost:8081/api/transactions" `
  -Headers @{
    "Authorization" = "Bearer SECRETARY_TOKEN"
    "Content-Type"  = "application/json"
  } `
  -Body '{ "customer": "John Doe", "vendor_id": "VENDOR123", "amount": 500 }'
```

Expected response:
```json
{
  "detail": "Access denied: role secretary not allowed"
}
```

### 2. Try to create a transaction without token (should fail)

```powershell
curl -Method POST `
  -Uri "http://localhost:8081/api/transactions" `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{ "customer": "John Doe", "vendor_id": "VENDOR123", "amount": 500 }'
```

Expected response:
```json
{
  "detail": "Not authenticated"
}
``` 