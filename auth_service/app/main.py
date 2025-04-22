import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import uuid
import json
from starlette.responses import JSONResponse

try:
    # Try importing from app module first
    from app.models import Token, UserCreate, UserResponse, LoginRequest
    from app.users import get_user, create_user, delete_user, initialize_users
    from app.auth import authenticate_user, create_access_token, verify_token, cleanup_expired_tokens
    from app.logger import get_logger
except ImportError:
    # Fall back to direct imports when running as script
    from models import Token, UserCreate, UserResponse, LoginRequest
    from users import get_user, create_user, delete_user, initialize_users
    from auth import authenticate_user, create_access_token, verify_token, cleanup_expired_tokens
    from logger import get_logger

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Set up logger
logger = get_logger("auth_service", "auth_service.log")

# Define startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run during startup
    initialize_users()  # Create initial users
    logger.info("Auth Service started")
    
    # Start token cleanup task
    cleanup_task = None
    
    # Function to run token cleanup periodically
    async def cleanup_loop():
        while True:
            cleanup_expired_tokens()
            await asyncio.sleep(60)  # Run every minute
    
    # Launch background task
    cleanup_task = asyncio.create_task(cleanup_loop())
    
    # Return control to FastAPI
    yield
    
    # Code to run during shutdown
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            pass
        logger.info("Auth Service shutting down")

# Create FastAPI app
app = FastAPI(
    title="Authentication Service",
    description="Service for user auth and token management",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple function to log request info
def log_request_info(request: Request, body=None):
    """Log request information including body if provided"""
    client_ip = request.client.host if request.client else "unknown"
    port = os.environ.get("AUTHENTICATION_PORT", 8080)
    destination = f"auth_service:{port}{request.url.path}"
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": client_ip,
        "destination": destination,
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers)
    }
    
    if body is not None:
        log_data["body"] = body
        
    logger.info(f"Request: {json.dumps(log_data)}")

# Simple function to log response info
def log_response_info(request: Request, status_code: int, body=None):
    """Log response information including body if provided"""
    client_ip = request.client.host if request.client else "unknown"
    port = os.environ.get("AUTHENTICATION_PORT", 8080)
    source = f"auth_service:{port}{request.url.path}"
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "destination": client_ip,
        "status_code": status_code,
        "headers": {"content-type": "application/json"}
    }
    
    if body is not None:
        log_data["body"] = body
        
    logger.info(f"Response: {json.dumps(log_data)}")

# Custom response class that logs the response
class LoggingJSONResponse(JSONResponse):
    def __init__(self, content, status_code=200, request=None, **kwargs):
        super().__init__(content=content, status_code=status_code, **kwargs)
        if request:
            log_response_info(request, status_code, content)

# API endpoint: Login and get token
@app.post("/api/auth/login", response_model=Token)
async def login_for_access_token(login_data: LoginRequest, request: Request):
    # Log the request body
    log_request_info(request, login_data.dict())
    
    # Authenticate user with provided credentials
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        logger.warning(f"Failed login: {login_data.username}")
        error_response = {"detail": "Incorrect username or password"}
        log_response_info(request, status.HTTP_401_UNAUTHORIZED, error_response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create a token containing user role
    token = create_access_token(
        username=user.username,
        role=user.role
    )
    
    # Create response
    response_data = {"access_token": token, "token_type": "bearer"}
    
    logger.info(f"Login success: {user.username}")
    return LoggingJSONResponse(content=response_data, request=request)

# API endpoint: Verify token validity
@app.get("/api/auth/verify")
async def verify_token_endpoint(token: str, request: Request):
    # Log request
    log_request_info(request)
    
    # Check if token is valid
    logger.info(f"Verifying token: {token[:10]}...")
    
    token_data = verify_token(token)
    if not token_data:
        logger.warning("Token verification failed")
        response_data = {"valid": False}
        return LoggingJSONResponse(content=response_data, request=request)
    
    logger.info(f"Token valid for {token_data['username']}, role: {token_data['role']}")
    response_data = {"valid": True, "role": token_data["role"]}
    return LoggingJSONResponse(content=response_data, request=request)

# API endpoint: Create new user (admin only)
@app.post("/api/users", response_model=UserResponse)
async def create_new_user(user: UserCreate, token: str, request: Request):
    # Log request
    log_request_info(request, user.dict())
    
    # Verify token and check admin permissions
    token_data = verify_token(token)
    if not token_data or token_data["role"] != "admin":
        logger.warning(f"Unauthorized user management attempt")
        error_response = {"detail": "Only administrators can manage users"}
        log_response_info(request, status.HTTP_403_FORBIDDEN, error_response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage users"
        )
    
    # Check if username already exists
    if get_user(user.username):
        logger.warning(f"Duplicate user: {user.username}")
        error_response = {"detail": "Username already exists"}
        log_response_info(request, status.HTTP_400_BAD_REQUEST, error_response)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create the new user
    db_user = create_user(user)
    logger.info(f"User created: {db_user.username}")
    response_data = {"username": db_user.username, "role": db_user.role}
    return LoggingJSONResponse(content=response_data, request=request)

# API endpoint: Delete a user (admin only)
@app.delete("/api/users/{username}")
async def remove_user(username: str, token: str, request: Request):
    # Log request
    log_request_info(request)
    
    # Verify token and check admin permissions
    token_data = verify_token(token)
    if not token_data or token_data["role"] != "admin":
        logger.warning(f"Unauthorized user deletion attempt")
        error_response = {"detail": "Only administrators can delete users"}
        log_response_info(request, status.HTTP_403_FORBIDDEN, error_response)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete users"
        )
    
    # Delete the user
    success = delete_user(username)
    if not success:
        logger.warning(f"User not found: {username}")
        error_response = {"detail": "User not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    logger.info(f"User deleted: {username}")
    response_data = {"detail": "User deleted successfully"}
    return LoggingJSONResponse(content=response_data, request=request)

# Run the app if script is executed directly
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("AUTHENTICATION_PORT", 8080))
    print(f"Starting Auth Service on port {port}")
    uvicorn.run("app.main:app", host="localhost", port=port, reload=True)