import os
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.models import Token, UserCreate, UserResponse, User
from app.database import get_user, create_user, delete_user, initialize_users
from app.auth import authenticate_user, create_access_token, get_current_user, verify_token
from app.logger import get_logger, RequestResponseFilter
import logging
import uuid

# Create logs directory if it doesn't exist
os.makedirs("../../logs", exist_ok=True)

# Create and configure the application
app = FastAPI(
    title="Authentication Service",
    description="Service for user authentication and token management",
    version="1.0.0"
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logger
logger = get_logger("auth_service", "auth_service.log")

# Initialize users on startup
@app.on_event("startup")
def startup_event():
    initialize_users()
    logger.info("Authentication Service started and users initialized")

# Middleware for request/response logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    client_host = request.client.host if request.client else "unknown"
    
    # Configure logger with request details
    log_filter = RequestResponseFilter(
        source=client_host,
        destination=f"{request.url.path}",
        headers=dict(request.headers)
    )
    
    for handler in logger.handlers:
        handler.addFilter(log_filter)
    
    logger.info(f"Request received: {request.method} {request.url.path}")
    
    # Process the request
    response = await call_next(request)
    
    logger.info(f"Response sent: {response.status_code}")
    
    # Clean up filters
    for handler in logger.handlers:
        handler.removeFilter(log_filter)
    
    return response

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in successfully: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}

@app.post("/verify-token")
async def verify_token_endpoint(token: str):
    """Verify if a token is valid and return the payload"""
    payload = verify_token(token)
    if not payload:
        logger.warning("Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    logger.info(f"Token verified for user: {payload.get('sub')}")
    return {"valid": True, "payload": payload}

# Admin endpoints for user management
@app.post("/users", response_model=UserResponse)
async def create_new_user(
    user: UserCreate,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        logger.warning(f"Unauthorized user management attempt by: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage users"
        )
    
    if get_user(user.username):
        logger.warning(f"Attempt to create duplicate user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    db_user = create_user(user)
    logger.info(f"New user created: {db_user.username}")
    return {"username": db_user.username, "role": db_user.role}

@app.delete("/users/{username}")
async def remove_user(
    username: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        logger.warning(f"Unauthorized user deletion attempt by: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    success = delete_user(username)
    if not success:
        logger.warning(f"Attempt to delete non-existent user: {username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User deleted: {username}")
    return {"detail": "User deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 