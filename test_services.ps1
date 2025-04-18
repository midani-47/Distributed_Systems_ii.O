#!/usr/bin/env pwsh
# Windows PowerShell script to test fraud detection services

Write-Host "`n=== Testing Fraud Detection Services ===`n" -ForegroundColor Cyan

# Function to test a service
function Test-ServiceEndpoint {
    param (
        [string]$Name,
        [string]$Url
    )
    
    Write-Host "Testing $Name... " -NoNewline
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "OK (Status code: $($response.StatusCode))" -ForegroundColor Green
            return $true
        } else {
            Write-Host "Failed (Status code: $($response.StatusCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "Failed to connect. Service may not be running." -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
        return $false
    }
}

# Test Authentication Service
$authServiceRunning = Test-ServiceEndpoint -Name "Authentication Service" -Url "http://localhost:8080/docs"

# Test Transaction Service
$transServiceRunning = Test-ServiceEndpoint -Name "Transaction Service" -Url "http://localhost:8081/docs"

# If both services are running, test authentication flow
if ($authServiceRunning -and $transServiceRunning) {
    Write-Host "`n=== Testing Authentication Flow ===`n" -ForegroundColor Cyan
    
    # Test authentication
    Write-Host "Getting authentication token... " -NoNewline
    try {
        $authData = @{
            username = "johndoe"
            password = "password123"
        } | ConvertTo-Json
        
        $response = Invoke-RestMethod -Uri "http://localhost:8080/token" `
            -Method Post `
            -Body $authData `
            -ContentType "application/json" `
            -ErrorAction Stop
        
        if ($response.access_token) {
            $token = $response.access_token
            Write-Host "Success! Token received." -ForegroundColor Green
            
            # Test accessing transactions API with token
            Write-Host "`nTesting Transaction API access... " -NoNewline
            try {
                $headers = @{
                    "Authorization" = "Bearer $token"
                }
                
                $transResponse = Invoke-RestMethod -Uri "http://localhost:8081/transactions" `
                    -Method Get `
                    -Headers $headers `
                    -ErrorAction Stop
                
                Write-Host "Success! Transaction API accessible." -ForegroundColor Green
                Write-Host "`nFound $(($transResponse | Measure-Object).Count) transactions in the response."
                
                Write-Host "`n✅ All tests passed successfully!" -ForegroundColor Green
            } catch {
                Write-Host "Failed to access Transaction API." -ForegroundColor Red
                Write-Host "Error: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "Failed to get authentication token." -ForegroundColor Red
        }
    } catch {
        Write-Host "Failed to authenticate." -ForegroundColor Red
        Write-Host "Error: $_" -ForegroundColor Red
    }
} else {
    Write-Host "`n❌ Cannot proceed with authentication tests because one or more services are not running." -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===`n" -ForegroundColor Cyan 