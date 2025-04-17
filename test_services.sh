#!/bin/bash

echo "================ SERVICE TEST =================";
echo "Testing if services are available and responding...";

# Test if the Authentication Service is running
echo "Checking Authentication Service...";
AUTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/docs)

if [ "$AUTH_RESPONSE" = "200" ]; then
    echo "✅ Authentication Service is running."
else
    echo "❌ Authentication Service is not available! Received HTTP code: $AUTH_RESPONSE"
    exit 1
fi

# Test if the Transaction Service is running
echo "Checking Transaction Service...";
TRANSACTION_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8081/docs)

if [ "$TRANSACTION_RESPONSE" = "200" ]; then
    echo "✅ Transaction Service is running."
else
    echo "❌ Transaction Service is not available! Received HTTP code: $TRANSACTION_RESPONSE"
    exit 1
fi

# Now test authentication
echo "Testing authentication...";
TOKEN_RESPONSE=$(curl -s -X 'POST' 'http://localhost:8080/token' \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=admin&password=admin')

if echo "$TOKEN_RESPONSE" | grep -q "access_token"; then
    # Extract token using basic text manipulation
    TOKEN=$(echo "$TOKEN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    
    echo "✅ Authentication successful."
    echo "Access token received."
    
    # Now test transaction API with token
    echo "Testing Transaction API with token..."
    TRANS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        http://localhost:8081/transactions)
    
    if [ "$TRANS_RESPONSE" = "200" ]; then
        echo "✅ Transaction API accessible with token."
        echo "All services are working correctly."
    else
        echo "❌ Failed to access Transaction API with token! Received HTTP code: $TRANS_RESPONSE"
        exit 1
    fi
else
    echo "❌ Authentication failed! Response:"
    echo "$TOKEN_RESPONSE"
    exit 1
fi

echo "===============================================";
echo "ALL TESTS PASSED! ✨";
echo "Services are running correctly.";
echo "==============================================="; 