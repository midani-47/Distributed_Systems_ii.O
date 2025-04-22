import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.models import UserInDB
from app.users import get_user, verify_password
import logging

# setting up the logger thingy
logger = logging.getLogger("auth_service")

# we keep tokens in memory cuz its easier for now
# format is like {token: {"username": str, "role": str, "expiry": datetime}}
tokens_db: Dict[str, dict] = {}

# tokens expire after this many minutes. maybe make longer?
TOKEN_EXPIRE_MINUTES = 30

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """
    Check if username exists and password is correct
    Returns the user object if valid, None otherwise
    """
    # grab user from db
    user = get_user(username)
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    
    # check if password matches. important!
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Wrong password: {username}")
        return None
    
    return user

def create_access_token(username: str, role: str) -> str:
    # make a random token with some bytes. more secure this way
    random_part = base64.b64encode(os.urandom(16)).decode('utf-8')
    
    # stick the role in the token so we know what they can do
    token = f"{random_part}|{role}"
    
    # set when it gonna expire
    expiry = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    
    # save token in our memory db
    tokens_db[token] = {
        "username": username,
        "role": role,
        "expiry": expiry
    }
    
    logger.info(f"Token created for: {username}")
    return token

def verify_token(token: str) -> Optional[dict]:
    # see if token exist in our db
    if token not in tokens_db:
        logger.warning("Unknown token")
        return None
    
    token_data = tokens_db[token]
    
    # tokens expire after a while for security
    if datetime.utcnow() > token_data["expiry"]:
        logger.warning(f"Expired token for: {token_data['username']}")
        # get rid of old token
        del tokens_db[token]
        return None
    
    # if we get here token is good
    return {
        "username": token_data["username"],
        "role": token_data["role"],
        "valid": True
    }

def cleanup_expired_tokens():
    # this clean up old tokens so we dont waste memory
    now = datetime.utcnow()
    
    # look for tokens that expired
    expired = [
        token for token, data in tokens_db.items() 
        if now > data["expiry"]
    ]
    
    # delete em
    for token in expired:
        username = tokens_db[token]['username']
        del tokens_db[token]
        logger.info(f"Removed expired token for: {username}")