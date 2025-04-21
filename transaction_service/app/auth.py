import os
import sys
import subprocess
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.logger import get_logger

# First try to ensure aiohttp is installed
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    print("aiohttp not found, attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aiohttp>=3.8.0"])
        import aiohttp
        AIOHTTP_AVAILABLE = True
        print("aiohttp installed successfully")
    except Exception as e:
        print(f"Failed to install aiohttp: {e}")
        print("Will use requests library as fallback")
        AIOHTTP_AVAILABLE = False
        import requests

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
        logger.info(f"Sending verification request to: {AUTH_SERVICE_URL}/api/auth/verify")
        
        if AIOHTTP_AVAILABLE:
            # Use aiohttp for async HTTP requests
            return await verify_token_aiohttp(token)
        else:
            # Use requests as fallback
            return verify_token_requests(token)
    
    except Exception as e:
        logger.error(f"Error connecting to auth service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

async def verify_token_aiohttp(token):
    """Use aiohttp to verify the token (async)"""
    try:
        # Use aiohttp for asynchronous HTTP requests
        async with aiohttp.ClientSession() as session:
            # Try the primary endpoint
            async with session.get(
                f"{AUTH_SERVICE_URL}/api/auth/verify",
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
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid authentication credentials"
                    )
                
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

def verify_token_requests(token):
    """Use synchronous requests to verify the token (fallback)"""
    try:
        # Use regular requests as fallback
        response = requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/verify",
            params={"token": token},
            timeout=10
        )
        
        # Log the response
        status_code = response.status_code
        logger.info(f"Auth service response status: {status_code}")
        print(f"[SERVICE-COMM] Auth Service -> Transaction | Response: {status_code}")
        
        if status_code != 200:
            logger.warning(f"Token verification failed with status {status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Parse JSON response
        verification_result = response.json()
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
        
    except requests.RequestException as e:
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