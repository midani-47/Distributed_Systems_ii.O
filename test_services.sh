#!/bin/bash

# Default configuration
AUTH_PORT=${AUTHENTICATION_PORT:-8080}
TRANS_PORT=${TRANSACTION_PORT:-8081}
USERNAME=${TEST_USERNAME:-admin}
PASSWORD=${TEST_PASSWORD:-admin123}

echo "==============================================="
echo "Testing Fraud Detection Services"
echo "==============================================="

# Helper function to check HTTP status code
check_service() {
    local url=$1
    local service_name=$2
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" -m 10)
    
    if [ "$http_code" -eq 200 ]; then
        echo "✅ $service_name is running (Status: $http_code)"
        return 0
    else
        echo "❌ $service_name returned error status: $http_code"
        return 1
    fi
}

# Test Authentication Service
auth_service_url="http://localhost:$AUTH_PORT/docs"
if ! check_service "$auth_service_url" "Authentication Service"; then
    echo "Cannot proceed with tests because Authentication Service is not running."
    exit 1
fi

# Test Transaction Service
transaction_service_url="http://localhost:$TRANS_PORT/docs"
if ! check_service "$transaction_service_url" "Transaction Service"; then
    echo "Cannot proceed with tests because Transaction Service is not running."
    exit 1
fi

# Test Authentication
echo ""
echo "Testing authentication..."
auth_response=$(curl -s -X POST "http://localhost:$AUTH_PORT/token" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME&password=$PASSWORD")

echo "DEBUG - Auth response: $auth_response"

# Extract token
token=$(echo "$auth_response" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$token" ]; then
    echo "❌ Authentication failed. No token received."
    echo "Response: $auth_response"
    exit 1
else
    echo "✅ Authentication successful! Token received."
fi

# Test Transaction API access with token
echo ""
echo "Testing Transaction API access..."
transactions_response=$(curl -s -X GET "http://localhost:$TRANS_PORT/transactions" \
    -H "Authorization: Bearer $token")

echo "DEBUG - Transactions response: $transactions_response"

# Check if response seems valid (contains data structure of transactions)
if [[ "$transactions_response" == *"["* ]] || [[ "$transactions_response" == *"{"* ]]; then
    echo "✅ Successfully accessed Transaction API!"
    # Count transactions (simple estimation by counting opening braces)
    transaction_count=$(echo "$transactions_response" | grep -o "{" | wc -l)
    echo "Retrieved approximately $transaction_count transaction(s)"
else
    echo "❌ Transaction API access failed."
    echo "Response: $transactions_response"
    exit 1
fi

echo ""
echo "✅ All tests passed! Services are running properly." 