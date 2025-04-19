import os
from datetime import timedelta, datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
try:
    # First try relative imports for running as module
    from app.models import Token, UserCreate, UserResponse, User, LoginRequest
    from app.database import get_user, create_user, delete_user, initialize_users
    from app.auth import authenticate_user, create_access_token, verify_token, cleanup_expired_tokens
    from app.logger import get_logger, RequestResponseFilter
except ImportError:
    # Fall back to direct imports for running directly
    from models import Token, UserCreate, UserResponse, User, LoginRequest
    from database import get_user, create_user, delete_user, initialize_users
    from auth import authenticate_user, create_access_token, verify_token, cleanup_expired_tokens
    from logger import get_logger, RequestResponseFilter
import logging
import uuid
import json
import asyncio

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Define lifespan context manager for FastAPI startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize users on startup
    initialize_users()
    logger.info("Authentication Service started and users initialized")
    
    # Run token cleanup periodically
    cleanup_task = None
    
    async def cleanup_loop():
        while True:
            cleanup_expired_tokens()
            await asyncio.sleep(60)  # Run every minute
    
    # Start background task
    cleanup_task = asyncio.create_task(cleanup_loop())
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown: Cancel the cleanup task
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("Authentication Service shutting down")

# Create and configure the application
app = FastAPI(
    title="Authentication Service",
    description="Service for user authentication and token management",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
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

# Middleware for request/response logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    client_host = request.client.host if request.client else "unknown"
    
    # Log request path and method without reading the body
    port = os.environ.get("AUTHENTICATION_PORT", 8080)
    
    # Prepare request logging data
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "source": client_host,
        "destination": f"auth_service:{port}{request.url.path}",
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
    }
    
    # Print detailed request log to terminal
    print(f"\n[AUTH-REQUEST] {datetime.utcnow().isoformat()} | {request.method} {request.url.path}")
    print(f"  Source: {client_host}")
    print(f"  Headers: {json.dumps(dict(request.headers), indent=2)}")
    print(f"  Query params: {json.dumps(dict(request.query_params), indent=2)}")
    
    # Also log to file
    logger.info(f"Request: {json.dumps(log_data)}")
    
    # Process the request without trying to read/reconstruct the body
    response = await call_next(request)
    
    # Create a response log
    response_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "statusCode": response.status_code,
        "headers": dict(response.headers),
    }
    
    # Print response log to terminal
    print(f"[AUTH-RESPONSE] {datetime.utcnow().isoformat()} | Status: {response.status_code}")
    print(f"  Headers: {json.dumps(dict(response.headers), indent=2)}")
    
    # Also log to file
    logger.info(f"Response: {json.dumps(response_log)}")
    
    return response

# Authentication endpoints
@app.post("/api/auth/login", response_model=Token)
async def login_for_access_token_legacy(login_data: LoginRequest):
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
    return {"access_token": token, "token_type": "bearer"}

@app.get("/api/auth/verify")
async def verify_token_endpoint(token: str):
    """Verify if a token is valid and return role information"""
    # Add debug logging
    logger.info(f"Received verification request for token: {token[:10] if len(token) > 10 else token}...")
    
    token_data = verify_token(token)
    if not token_data:
        logger.warning("Token verification failed")
        return {"valid": False}
    
    logger.info(f"Token verified for user: {token_data['username']}, role: {token_data['role']}")
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
    # Get port from environment variable or use default 8080
    port = int(os.environ.get("AUTHENTICATION_PORT", 8080))
    print(f"Starting Authentication Service on port {port} with debug mode...")
    uvicorn.run("app.main:app", host="localhost", port=port, reload=True) 