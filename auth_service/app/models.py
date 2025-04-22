from pydantic import BaseModel
from typing import Optional

# base user model with core identity and authentication properties
class User(BaseModel):
    """Basic user data model"""
    username: str
    hashed_password: str
    role: str  # possible values: "admin", "secretary", "agent"
    disabled: bool = False

# user representation for database storage
class UserInDB(User):
    """User stored in database"""
    pass

# data structure for user creation requests
class UserCreate(BaseModel):
    """Data needed to create a new user"""
    username: str
    password: str  # plain text password that will be hashed before storage
    role: str

# user data returned after creation operation
class UserResponse(BaseModel):
    """User data returned after creation"""
    username: str
    role: str

# authentication request structure
class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str

# authentication response containing token
class Token(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"

# structure of data encoded in authentication tokens
class TokenData(BaseModel):
    """Data stored in a token"""
    username: Optional[str] = None
    role: Optional[str] = None