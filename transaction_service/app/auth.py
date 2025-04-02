import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.logger import get_logger

# Configure authentication settings
AUTH_SERVICE_URL = "http://localhost:8000"  # URL of the authentication service
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{AUTH_SERVICE_URL}/token")

# Configure logger
logger = get_logger("transaction_service.auth")

async def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Verify token with the Authentication Service
    """
    try:
        response = requests.post(
            f"{AUTH_SERVICE_URL}/verify-token",
            params={"token": token}
        )
        
        if response.status_code != 200:
            logger.warning(f"Token verification failed with status {response.status_code}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user data from token payload
        payload = response.json().get("payload", {})
        username = payload.get("sub")
        role = payload.get("role")
        
        if not username or not role:
            logger.warning("Token payload missing required fields")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token data",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"Token verified for user: {username}")
        return {"username": username, "role": role}
    
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
            logger.warning(f"Access denied for user {user_data.get('username')} with role {user_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: role {user_role} not allowed"
            )
        
        return user_data
    
    return role_checker 