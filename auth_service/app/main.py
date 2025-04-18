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
    
    # Log basic request info without body to avoid streaming issues
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "source": client_host,
        "destination": f"auth_service:{port}{request.url.path}",
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
    }
    
    logger.info(f"Request started: {json.dumps(log_data)}")
    
    # Process the request without trying to read/reconstruct the body
    response = await call_next(request)
    
    # Create a response log
    response_log = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "statusCode": response.status_code,
    }
    
    logger.info(f"Response: {json.dumps(response_log)}")
    
    return response

# Authentication endpoints
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
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

# Also keep the original endpoint for backward compatibility
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

# Also add a more standard OAuth2 verification endpoint
@app.get("/verify-token")
async def verify_token_standard(token: str = None, authorization: str = None):
    """Alternative token verification endpoint supporting both query param and header"""
    # Get token from either query param or Authorization header
    actual_token = None
    
    if authorization and authorization.startswith("Bearer "):
        actual_token = authorization[7:]  # Remove 'Bearer ' prefix
        logger.info("Token extracted from Authorization header")
    elif token:
        actual_token = token
        logger.info("Token extracted from query parameter")
    else:
        logger.warning("No token provided")
        return {"valid": False, "error": "No token provided"}
    
    logger.info(f"Verifying token: {actual_token[:10] if len(actual_token) > 10 else actual_token}...")
    token_data = verify_token(actual_token)
    
    if not token_data:
        logger.warning("Token verification failed")
        return {"valid": False, "error": "Invalid token"}
    
    logger.info(f"Token verified for user: {token_data['username']}, role: {token_data['role']}")
    return {"valid": True, "role": token_data["role"], "username": token_data["username"]}

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
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 