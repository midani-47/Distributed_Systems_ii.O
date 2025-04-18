import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.models import TokenData, UserInDB
from app.database import get_user, verify_password
import logging

# Configure logger
logger = logging.getLogger("auth_service")

# In-memory token storage
# Structure: {token: {"username": username, "role": role, "expiry": datetime}}
tokens_db: Dict[str, dict] = {}

# Token expiration time in minutes
TOKEN_EXPIRE_MINUTES = 30

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Verify username and password and return user if valid"""
    user = get_user(username)
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Invalid password for user: {username}")
        return None
    return user

def create_access_token(username: str, role: str) -> str:
    """Generate a token with expiry timestamp"""
    # Generate random bytes and encode in base64
    random_bytes = os.urandom(16)
    token_part = base64.b64encode(random_bytes).decode('utf-8')
    
    # Create token as per assignment requirements: Base64(randomBytes) + "|" + role
    token = f"{token_part}|{role}"
    
    # Store token with expiry time
    expiry = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    tokens_db[token] = {
        "username": username,
        "role": role,
        "expiry": expiry
    }
    
    logger.info(f"Created token for user: {username}, token value: {token[:10]}...")
    logger.info(f"Total tokens in DB: {len(tokens_db)}")
    return token

def verify_token(token: str) -> Optional[dict]:
    """Verify token exists and not expired, return user data if valid"""
    logger.info(f"Verifying token: {token[:10]}...")
    logger.info(f"Total tokens in DB: {len(tokens_db)}")
    logger.info(f"Known tokens: {[t[:10] for t in tokens_db.keys()]}")
    
    if token not in tokens_db:
        logger.warning("Token not found in database")
        return None
    
    token_data = tokens_db[token]
    
    # Check if token is expired
    if datetime.utcnow() > token_data["expiry"]:
        logger.warning(f"Token expired for user: {token_data['username']}")
        # Remove expired token
        del tokens_db[token]
        return None
    
    logger.info(f"Token verified for user: {token_data['username']}")
    return {
        "username": token_data["username"],
        "role": token_data["role"],
        "valid": True
    }

# Clean up expired tokens
def cleanup_expired_tokens():
    """Remove expired tokens from the token database"""
    current_time = datetime.utcnow()
    expired_tokens = [
        token for token, data in tokens_db.items() 
        if current_time > data["expiry"]
    ]
    
    for token in expired_tokens:
        logger.info(f"Removing expired token for user: {tokens_db[token]['username']}")
        del tokens_db[token] 