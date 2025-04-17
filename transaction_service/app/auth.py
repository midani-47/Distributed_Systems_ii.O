import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.logger import get_logger

# Configure authentication settings
AUTH_SERVICE_URL = "http://localhost:8080"  # URL of the authentication service
security = HTTPBearer()

# Configure logger
logger = get_logger("transaction_service.auth")

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify token with the Authentication Service
    """
    token = credentials.credentials
    
    # Remove "Bearer " prefix if included again in the token
    if token.startswith("Bearer "):
        token = token[7:]
    
    try:
        response = requests.get(
            f"{AUTH_SERVICE_URL}/api/auth/verify",
            params={"token": token}
        )
        
        if response.status_code != 200:
            logger.warning(f"Token verification failed with status {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Extract verification result
        verification_result = response.json()
        
        if not verification_result.get("valid", False):
            logger.warning("Token reported as invalid by auth service")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Extract role from token
        role = verification_result.get("role")
        
        if not role:
            logger.warning("Token missing role information")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token data"
            )
        
        logger.info(f"Token verified with role: {role}")
        return {"role": role}
    
    except requests.RequestException as e:
        logger.error(f"Error connecting to auth service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable"
        )

def require_role(allowed_roles):
    """
    Dependency to check if user has required role
    """
    async def role_checker(user_data: dict = Depends(verify_token)):
        user_role = user_data.get("role")
        
        if user_role not in allowed_roles:
            logger.warning(f"Access denied for role {user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role {user_role} not allowed"
            )
        
        return user_data
    
    return role_checker 