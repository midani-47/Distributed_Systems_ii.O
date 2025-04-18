# Windows PowerShell script to test services
param (
    [int]$auth_port = 8080,
    [int]$transaction_port = 8081,
    [string]$username = "admin",
    [string]$password = "admin123"
)

Write-Host "==============================================="
Write-Host "Testing Fraud Detection Services"
Write-Host "==============================================="

# Helper function to check HTTP status code
function Test-HttpStatusCode {
    param (
        [string]$url,
        [string]$service_name
    )
    
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10
        Write-Host "✅ $service_name is running (Status: $($response.StatusCode))"
        return $true
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        if ($statusCode) {
            Write-Host "❌ $service_name returned error status: $statusCode"
        } else {
            Write-Host "❌ $service_name is not responding. Make sure it's running."
        }
        return $false
    }
}

# Test Authentication Service
$auth_service_url = "http://localhost:$auth_port/docs"
$auth_running = Test-HttpStatusCode -url $auth_service_url -service_name "Authentication Service"

if (-not $auth_running) {
    Write-Host "Cannot proceed with tests because Authentication Service is not running."
    exit 1
}

# Test Transaction Service
$transaction_service_url = "http://localhost:$transaction_port/docs"
$transaction_running = Test-HttpStatusCode -url $transaction_service_url -service_name "Transaction Service"

if (-not $transaction_running) {
    Write-Host "Cannot proceed with tests because Transaction Service is not running."
    exit 1
}

# Test Authentication
Write-Host "`nTesting authentication..."
try {
    $auth_data = @{
        "username" = $username
        "password" = $password
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:$auth_port/token" -Method Post -Form $auth_data -UseBasicParsing
    
    Write-Host "DEBUG - Auth response: $($response | ConvertTo-Json -Compress)"
    
    if ($response.access_token) {
        Write-Host "✅ Authentication successful! Token received."
        $token = $response.access_token
    } else {
        Write-Host "❌ Authentication failed. No token received."
        exit 1
    }
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "❌ Authentication failed with status: $statusCode"
    Write-Host $_.Exception.Message
    exit 1
}

# Test Transaction API access with token
Write-Host "`nTesting Transaction API access..."
try {
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:$transaction_port/transactions" -Method Get -Headers $headers -UseBasicParsing
    
    Write-Host "DEBUG - Transactions response: $($response | ConvertTo-Json -Compress)"
    
    Write-Host "✅ Successfully accessed Transaction API!"
    Write-Host "Retrieved $(($response | Measure-Object).Count) transaction(s)"
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "❌ Transaction API access failed with status: $statusCode"
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host "`n✅ All tests passed! Services are running properly." 