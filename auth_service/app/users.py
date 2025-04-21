from passlib.context import CryptContext
from app.models import User, UserInDB, UserCreate
import sys
import subprocess
import logging

# Try to ensure bcrypt is installed
try:
    # Explicitly install bcrypt first if needed
    try:
        import bcrypt
    except ImportError:
        print("bcrypt not found, attempting to install...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "bcrypt>=4.0.1,<5.0.0"])
            import bcrypt
            print("bcrypt installed successfully")
        except Exception as e:
            print(f"Failed to install bcrypt: {e}")
            print("Please install bcrypt manually with: pip install bcrypt>=4.0.1,<5.0.0")
            # Use a fallback scheme if bcrypt isn't available
            pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    
    # Set up the password context - this will work regardless of bcrypt version
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Quick test to verify bcrypt functionality
    test_hash = pwd_context.hash("test")
    if not pwd_context.verify("test", test_hash):
        print("Warning: bcrypt verification failed, using fallback")
        pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
    
except Exception as e:
    print(f"Error setting up password hashing: {e}")
    print("Using SHA-256 as fallback")
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# In-memory user database
users_db = {}

# Add some initial users for testing
def initialize_users():
    users = [
        UserCreate(username="admin", password="admin123", role="admin"),
        UserCreate(username="secretary", password="secretary123", role="secretary"),
        UserCreate(username="agent", password="agent123", role="agent")
    ]
    
    for user in users:
        create_user(user)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str) -> UserInDB:
    if username in users_db:
        user_dict = users_db[username]
        return UserInDB(**user_dict)
    return None


def create_user(user: UserCreate) -> UserInDB:
    hashed_password = get_password_hash(user.password)
    db_user = UserInDB(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    users_db[user.username] = db_user.dict()
    return db_user


def delete_user(username: str) -> bool:
    if username in users_db:
        del users_db[username]
        return True
    return False 