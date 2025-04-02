from pydantic import BaseModel
from typing import Optional, List


class User(BaseModel):
    username: str
    hashed_password: str
    role: str  # Can be "admin", "secretary", or "agent"
    disabled: bool = False


class UserInDB(User):
    pass


class UserCreate(BaseModel):
    username: str
    password: str
    role: str


class UserResponse(BaseModel):
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None 