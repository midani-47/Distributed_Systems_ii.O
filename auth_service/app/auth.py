import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.models import UserInDB
from app.users import get_user, verify_password
import logging

# Set up logger
logger = logging.getLogger("auth_service")

# Simple in-memory token storage
# Format: {token: {"username": str, "role": str, "expiry": datetime}}
tokens_db: Dict[str, dict] = {}

# How long tokens are valid for
TOKEN_EXPIRE_MINUTES = 30

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Check if username exists and password is correct
    Returns the user object if valid, None otherwise
    """
    # Get user from database
    user = get_user(username)
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    
    # Check password
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Wrong password: {username}")
        return None
    
    return user

def create_access_token(username: str, role: str) -> str:
    """
    Create a new authentication token
    Token format: base64(random bytes) + "|" + role
    """
    # Create random token part
    random_part = base64.b64encode(os.urandom(16)).decode('utf-8')
    
    # Combine with role to make full token
    token = f"{random_part}|{role}"
    
    # Set expiration time
    expiry = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    # Store token in database
    tokens_db[token] = {
        "username": username,
        "role": role,
        "expiry": expiry
    }
    
    logger.info(f"Token created for: {username}")
    return token

def verify_token(token: str) -> Optional[dict]:
    """
    Check if token exists and is still valid
    Returns user data if valid, None otherwise
    """
    # Check if token exists in database
    if token not in tokens_db:
        logger.warning("Unknown token")
        return None
    
    token_data = tokens_db[token]
    
    # Check if token has expired
    if datetime.utcnow() > token_data["expiry"]:
        logger.warning(f"Expired token for: {token_data['username']}")
        # Remove expired token
        del tokens_db[token]
        return None
    
    # Token is valid
    return {
        "username": token_data["username"],
        "role": token_data["role"],
        "valid": True
    }

def cleanup_expired_tokens():
    """
    Remove all expired tokens from database
    Should be called periodically
    """
    now = datetime.utcnow()
    
    # Find expired tokens
    expired = [
        token for token, data in tokens_db.items() 
        if now > data["expiry"]
    ]
    
    # Remove them
    for token in expired:
        username = tokens_db[token]['username']
        del tokens_db[token]
        logger.info(f"Removed expired token for: {username}")