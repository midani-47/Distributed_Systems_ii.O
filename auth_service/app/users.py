from passlib.context import CryptContext
from app.models import UserInDB, UserCreate

# using this for the password thingy bcrypt is cool
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# just a simple dictionary for users. not persistent tho
users_db = {}

def initialize_users():
    """
    Create default users for testing
    Creates admin, secretary and agent users
    """
    test_users = [
        UserCreate(username="admin", password="admin123", role="admin"),
        UserCreate(username="secretary", password="secretary123", role="secretary"),
        UserCreate(username="agent", password="agent123", role="agent")
    ]
    
    for user in test_users:
        create_user(user)

def get_password_hash(password: str) -> str:
    """
    Convert a plain password to a secure hash
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches a hash
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_user(username: str) -> UserInDB:
    """
    Get a user by username
    Returns None if user doesn't exist
    """
    if username in users_db:
        user_data = users_db[username]
        return UserInDB(**user_data)
    return None

def create_user(user: UserCreate) -> UserInDB:
    # this gonna hash the password so nobody can see it
    hashed_password = get_password_hash(user.password)
    
    # make a new user object with the hashed pwd
    new_user = UserInDB(
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    
    # save it to our dictionary database thingy
    users_db[user.username] = new_user.dict()
    return new_user

def delete_user(username: str) -> bool:
    # delete user if exists. pretty simple eh
    if username in users_db:
        del users_db[username]
        return True
    return False