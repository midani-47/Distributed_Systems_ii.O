from pydantic import BaseModel
from typing import Optional

# this is our base user model, nothing fancy
class User(BaseModel):
    """Basic user data model"""
    username: str
    hashed_password: str
    role: str  # can be "admin", "secretary", or "agent"
    disabled: bool = False

# user model with db stuff
class UserInDB(User):
    """User stored in database"""
    pass

# when someone wants to make a new user
class UserCreate(BaseModel):
    """Data needed to create a new user"""
    username: str
    password: str  # regular password we'll hash it later
    role: str

# what we send back after creating user
class UserResponse(BaseModel):
    """User data returned after creation"""
    username: str
    role: str

# for login requests
class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str

# the token we give to logged in users
class Token(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"

# whats inside the token
class TokenData(BaseModel):
    """Data stored in a token"""
    username: Optional[str] = None
    role: Optional[str] = None