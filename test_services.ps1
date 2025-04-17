# Windows PowerShell script to test if distributed services are working

Write-Host "================ SERVICE TEST =================" -ForegroundColor Cyan
Write-Host "Testing if services are available and responding..." -ForegroundColor Cyan

# Test if the Authentication Service is running
Write-Host "Checking Authentication Service..." -ForegroundColor Yellow
try {
    $authResponse = Invoke-WebRequest -Uri "http://localhost:8080/docs" -UseBasicParsing
    if ($authResponse.StatusCode -eq 200) {
        Write-Host "✅ Authentication Service is running." -ForegroundColor Green
    } else {
        Write-Host "❌ Authentication Service returned unexpected status: $($authResponse.StatusCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Authentication Service is not available! Error: $_" -ForegroundColor Red
    exit 1
}

# Test if the Transaction Service is running
Write-Host "Checking Transaction Service..." -ForegroundColor Yellow
try {
    $transResponse = Invoke-WebRequest -Uri "http://localhost:8081/docs" -UseBasicParsing
    if ($transResponse.StatusCode -eq 200) {
        Write-Host "✅ Transaction Service is running." -ForegroundColor Green
    } else {
        Write-Host "❌ Transaction Service returned unexpected status: $($transResponse.StatusCode)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Transaction Service is not available! Error: $_" -ForegroundColor Red
    exit 1
}

# Now test authentication
Write-Host "Testing authentication..." -ForegroundColor Yellow
try {
    $authBody = "username=admin&password=admin"
    $tokenResponse = Invoke-WebRequest -Uri "http://localhost:8080/token" -Method Post -Body $authBody -ContentType "application/x-www-form-urlencoded" -UseBasicParsing
    $tokenData = $tokenResponse.Content | ConvertFrom-Json
    
    if ($tokenData.access_token) {
        $token = $tokenData.access_token
        Write-Host "✅ Authentication successful." -ForegroundColor Green
        Write-Host "Access token received." -ForegroundColor Green
        
        # Now test Transaction API with token
        Write-Host "Testing Transaction API with token..." -ForegroundColor Yellow
        $headers = @{
            "Authorization" = "Bearer $token"
        }
        
        try {
            $transDataResponse = Invoke-WebRequest -Uri "http://localhost:8081/transactions" -Headers $headers -UseBasicParsing
            if ($transDataResponse.StatusCode -eq 200) {
                Write-Host "✅ Transaction API accessible with token." -ForegroundColor Green
                Write-Host "All services are working correctly." -ForegroundColor Green
            } else {
                Write-Host "❌ Transaction API returned unexpected status: $($transDataResponse.StatusCode)" -ForegroundColor Red
                exit 1
            }
        } catch {
            Write-Host "❌ Failed to access Transaction API with token! Error: $_" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "❌ Authentication failed! Token not found in response." -ForegroundColor Red
        Write-Host "Response content: $($tokenResponse.Content)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Authentication failed! Error: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
    exit 1
}

Write-Host "===============================================" -ForegroundColor Green
Write-Host "ALL TESTS PASSED! ✨" -ForegroundColor Green
Write-Host "Services are running correctly." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green 