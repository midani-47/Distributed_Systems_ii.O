import os
from datetime import timedelta, datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from app.models import Token, UserCreate, UserResponse, User, LoginRequest
from app.database import get_user, create_user, delete_user, initialize_users
from app.auth import authenticate_user, create_access_token, verify_token, cleanup_expired_tokens
from app.logger import get_logger, RequestResponseFilter
import logging
import uuid
import json

# Create logs directory if it doesn't exist
os.makedirs("../../logs", exist_ok=True)

# Create and configure the application
app = FastAPI(
    title="Authentication Service",
    description="Service for user authentication and token management",
    version="1.0.0",
    docs_url="/docs"
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
    
    # Read request body
    body = b""
    async for chunk in request.stream():
        body += chunk
    
    # Log request
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": client_host,
        "destination": f"auth_service:8000{request.url.path}",
        "headers": dict(request.headers),
        "metadata": {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
        }
    }
    
    # Log body if it exists and is JSON
    if body:
        try:
            log_data["body"] = json.loads(body)
        except:
            log_data["body"] = body.decode('utf-8', errors='replace')
    
    logger.info(f"Request: {json.dumps(log_data)}")
    
    # Create a new request with the already read body
    new_request = Request(
        scope=request.scope,
        receive=request._receive,
    )
    
    # Process the request
    response = await call_next(new_request)
    
    # Create a response log
    response_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "statusCode": response.status_code,
        "headers": dict(response.headers),
    }
    
    logger.info(f"Response: {json.dumps(response_log)}")
    
    return response

# Run token cleanup periodically
@app.on_event("startup")
async def startup_cleanup_task():
    import asyncio
    
    async def cleanup_task():
        while True:
            cleanup_expired_tokens()
            await asyncio.sleep(60)  # Run every minute
    
    # Start background task
    asyncio.create_task(cleanup_task())

# Authentication endpoints
@app.post("/api/auth/login", response_model=Token)
async def login_for_access_token(login_data: LoginRequest):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Generate token with username and role
    token = create_access_token(
        username=user.username,
        role=user.role
    )
    
    logger.info(f"User logged in successfully: {user.username}")
    return {"token": token}

@app.get("/api/auth/verify")
async def verify_token_endpoint(token: str):
    """Verify if a token is valid and return role information"""
    token_data = verify_token(token)
    if not token_data:
        logger.warning("Token verification failed")
        return {"valid": False}
    
    logger.info(f"Token verified for user: {token_data['username']}")
    return {"valid": True, "role": token_data["role"]}

# Admin endpoints for user management
@app.post("/api/users", response_model=UserResponse)
async def create_new_user(user: UserCreate, token: str):
    token_data = verify_token(token)
    if not token_data or token_data["role"] != "admin":
        logger.warning(f"Unauthorized user management attempt")
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

@app.delete("/api/users/{username}")
async def remove_user(username: str, token: str):
    token_data = verify_token(token)
    if not token_data or token_data["role"] != "admin":
        logger.warning(f"Unauthorized user deletion attempt")
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