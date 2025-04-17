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


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    token: str


class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

    class Config:
        # Support both new and old pydantic
        try:
            from_attributes = True
        except ImportError:
            # Fallback for older pydantic
            orm_mode = True 