from pydantic import BaseModel
from typing import Optional

# Basic user model
class User(BaseModel):
    """Basic user data model"""
    username: str
    hashed_password: str
    role: str  # "admin", "secretary", or "agent"
    disabled: bool = False

# User in database
class UserInDB(User):
    """User stored in database"""
    pass

# Model for creating new users
class UserCreate(BaseModel):
    """Data needed to create a new user"""
    username: str
    password: str  # Plain password (will be hashed)
    role: str

# Response after creating a user
class UserResponse(BaseModel):
    """User data returned after creation"""
    username: str
    role: str

# Login request data
class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str

# Authentication token
class Token(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"

# Token data
class TokenData(BaseModel):
    """Data stored in a token"""
    username: Optional[str] = None
    role: Optional[str] = None