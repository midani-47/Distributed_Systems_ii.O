import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.models import UserInDB
from app.users import get_user, verify_password
import logging

# initializing logger for authentication events
logger = logging.getLogger("auth_service")

# storing tokens in memory for simplicity
tokens_db: Dict[str, dict] = {}

# token expiration time in minutes
TOKEN_EXPIRE_MINUTES = 30

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Check if username exists and password is correct
    Returns the user object if valid, None otherwise
    """
    # retrieving user from database
    user = get_user(username)
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    
    # verifying password against stored hash
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Wrong password: {username}")
        return None
    
    return user

def create_access_token(username: str, role: str) -> str:
    # generating random token component for security
    random_part = base64.b64encode(os.urandom(16)).decode('utf-8')
    
    # embedding role information in token structure
    token = f"{random_part}|{role}"
    
    # calculating token expiration time
    expiry = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    # storing token in memory database with metadata
    tokens_db[token] = {
        "username": username,
        "role": role,
        "expiry": expiry
    }
    
    logger.info(f"Token created for: {username}")
    return token

def verify_token(token: str) -> Optional[dict]:
    # checking if token exists in database
    if token not in tokens_db:
        logger.warning("Unknown token")
        return None
    
    token_data = tokens_db[token]
    
    # validating token expiration status
    if datetime.utcnow() > token_data["expiry"]:
        logger.warning(f"Expired token for: {token_data['username']}")
        # removing expired token
        del tokens_db[token]
        return None
    
    # token validated successfully
    return {
        "username": token_data["username"],
        "role": token_data["role"],
        "valid": True
    }

def cleanup_expired_tokens():
    # performing maintenance on token database to remove stale entries
    now = datetime.utcnow()
    
    # identifying expired tokens
    expired = [
        token for token, data in tokens_db.items() 
        if now > data["expiry"]
    ]
    
    # removing expired tokens
    for token in expired:
        username = tokens_db[token]['username']
        del tokens_db[token]
        logger.info(f"Removed expired token for: {username}")