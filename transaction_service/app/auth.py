import os
import aiohttp
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.logger import get_logger

# setting up where our auth service is. default localhost
AUTH_SERVICE_URL = os.environ.get("AUTH_SERVICE_URL", "http://localhost:8080")
security = HTTPBearer()

# setup the logger
logger = get_logger("transaction_service.auth")

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify token with the Authentication Service
    """
    token = credentials.credentials
    logger.info(f"Verifying token: {token[:10] if len(token) > 10 else token}...")
    
    # sometimes ppl send token with Bearer prefix multiple times by mistake
    # gotta fix that or it wont work
    while token.startswith("Bearer "):
        token = token[7:]
    
    logger.info(f"Clean token after removing Bearer prefix: {token[:10] if len(token) > 10 else token}")
    
    # log what we doing so we can debug
    print(f"\n[SERVICE-COMM] Transaction -> Auth Service | Verify Token")
    print(f"  Token: {token[:10]}...")
    
    try:
        # let auth service kno what we checking
        logger.info(f"Sending verification request to: {AUTH_SERVICE_URL}/verify-token")
        
        # use aiohttp for async requests cuz its faster
        async with aiohttp.ClientSession() as session:
            # try the new endpoint first with query param
            async with session.get(
                f"{AUTH_SERVICE_URL}/verify-token",
                params={"token": token},
                timeout=10  # dont wait forever
            ) as response:
                # save the status for logs
                status_code = response.status
                logger.info(f"Auth service response status: {status_code}")
                
                # print the result so we can see
                print(f"[SERVICE-COMM] Auth Service -> Transaction | Response: {status_code}")
                
                # if not 200 then somethings wrong
                if status_code != 200:
                    logger.warning(f"Token verification failed with status {status_code}")
                    
                    # maybe old endpoint works better?
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
                    # get the json data back
                    verification_result = await response.json()
                
                logger.info(f"Auth service response body: {str(verification_result)[:100]}")
                print(f"  Verification result: {verification_result}")
                
                # if token not valid gotta tell user
                if not verification_result.get("valid", False):
                    logger.warning("Token reported as invalid by auth service")
                    print(f"  Token invalid: {verification_result.get('error', 'Unknown error')}")
                    
                    # include any error from auth service
                    error_detail = verification_result.get("error", "Invalid token")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail=error_detail
                    )
                
                # need to get role to check permissions
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
        
        # if they dont have right role kick em out
        if role not in allowed_roles:
            logger.warning(f"Authorization failed: Role {role} not in {allowed_roles}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not authorized. Required roles: {', '.join(allowed_roles)}"
            )
        
        logger.info(f"Authorization successful for role: {role}")
        return user_data
    
    return role_checker 