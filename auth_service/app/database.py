from passlib.context import CryptContext
from app.models import User, UserInDB, UserCreate

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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