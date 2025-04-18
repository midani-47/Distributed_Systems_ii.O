import os
import aiohttp
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.logger import get_logger

# Configure authentication settings using environment variable or default to localhost
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8080")
security = HTTPBearer()

# Configure logger
logger = get_logger("transaction_service.auth")

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify token with the Authentication Service
    """
    token = credentials.credentials
    logger.info(f"Verifying token: {token[:10] if len(token) > 10 else token}...")
    
    # Fix double Bearer prefix issue
    # Remove all instances of "Bearer " from the token
    while token.startswith("Bearer "):
        token = token[7:]
    
    logger.info(f"Clean token after removing Bearer prefix: {token[:10] if len(token) > 10 else token}")
    
    # Log inter-service communication details to terminal
    print(f"\n[SERVICE-COMM] Transaction -> Auth Service | Verify Token")
    print(f"  Token: {token[:10]}...")
    
    try:
        # Log the request for debugging
        logger.info(f"Sending verification request to: {AUTH_SERVICE_URL}/verify-token")
        
        # Use aiohttp for asynchronous HTTP requests
        async with aiohttp.ClientSession() as session:
            # First try the new endpoint with standard query parameter
            async with session.get(
                f"{AUTH_SERVICE_URL}/verify-token",
                params={"token": token},
                timeout=10  # Add timeout to prevent hanging
            ) as response:
                # Log the response for debugging
                status_code = response.status
                logger.info(f"Auth service response status: {status_code}")
                
                # Print inter-service response details to terminal
                print(f"[SERVICE-COMM] Auth Service -> Transaction | Response: {status_code}")
                
                # Check for successful response
                if status_code != 200:
                    logger.warning(f"Token verification failed with status {status_code}")
                    
                    # Fallback to legacy endpoint if the new one fails
                    logger.info("Trying legacy verification endpoint...")
                    print(f"  Fallback to legacy endpoint: {AUTH_SERVICE_URL}/api/auth/verify")
                    
                    async with session.get(
                        f"{AUTH_SERVICE_URL}/api/auth/verify",
                        params={"token": token},
                        timeout=10
                    ) as legacy_response:
                        if legacy_response.status != 200:
                            logger.error(f"Both token verification endpoints failed")
                            print(f"  Both verification endpoints failed!")
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid authentication credentials"
                            )
                        verification_result = await legacy_response.json()
                        print(f"  Legacy response: {verification_result}")
                else:
                    # Parse the JSON response
                    verification_result = await response.json()
                
                logger.info(f"Auth service response body: {str(verification_result)[:100]}")
                print(f"  Verification result: {verification_result}")
                
                if not verification_result.get("valid", False):
                    logger.warning("Token reported as invalid by auth service")
                    print(f"  Token invalid: {verification_result.get('error', 'Unknown error')}")
                    
                    # Include any error message from the auth service
                    error_detail = verification_result.get("error", "Invalid token")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=error_detail
                    )
                
                # Extract role from token
                role = verification_result.get("role")
                
                if not role:
                    logger.warning("Token missing role information")
                    print(f"  Token missing role information!")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token data: missing role"
                    )
                
                logger.info(f"Token verified with role: {role}")
                print(f"  Token verified successfully with role: {role}")
                return {"role": role}
    
    except aiohttp.ClientError as e:
        logger.error(f"Error connecting to auth service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

def require_role(allowed_roles: list):
    """
    Check if the user has one of the allowed roles
    """
    async def role_checker(user_data: dict = Depends(verify_token)):
        role = user_data.get("role")
        
        if role not in allowed_roles:
            logger.warning(f"Authorization failed: Role {role} not in {allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized. Required roles: {', '.join(allowed_roles)}"
            )
        
        logger.info(f"Authorization successful for role: {role}")
        return user_data
    
    return role_checker 