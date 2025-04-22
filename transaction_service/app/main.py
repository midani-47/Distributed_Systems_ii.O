import os
import uuid
import json
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from starlette.responses import JSONResponse

try:
    # First try relative imports for running as module
    from app.models import Transaction, TransactionCreate, TransactionInDB, Prediction, PredictionCreate, TransactionStatus
    from app.database import get_db, create_tables, TransactionModel, ResultModel
    from app.auth import verify_token, require_role
    from app.logger import get_logger
except ImportError:
    # Fall back to direct imports for running directly
    from models import Transaction, TransactionCreate, TransactionInDB, Prediction, PredictionCreate, TransactionStatus
    from database import get_db, create_tables, TransactionModel, ResultModel
    from auth import verify_token, require_role
    from logger import get_logger

# Create logs directory
os.makedirs("logs", exist_ok=True)

# Set up logger
logger = get_logger("transaction_service", "transaction_service.log")

# Custom JSON encoder to handle datetime objects
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Define lifespan context manager for FastAPI startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    create_tables()
    logger.info("Transaction Service started and database initialized")
    yield
    # Shutdown: Any cleanup can go here if needed
    logger.info("Transaction Service shutting down")

# Create and configure the application
app = FastAPI(
    title="Transaction Service",
    description="Service for managing financial transactions and fraud predictions",
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

# Simple function to log request info
def log_request_info(request: Request, body=None):
    """Log request information including body if provided"""
    client_ip = request.client.host if request.client else "unknown"
    port = os.environ.get("TRANSACTION_PORT", 8081)
    destination = f"transaction_service:{port}{request.url.path}"
    
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
        
    logger.info(f"Request: {json.dumps(log_data, cls=DateTimeEncoder)}")

# Simple function to log response info
def log_response_info(request: Request, status_code: int, body=None):
    """Log response information including body if provided"""
    client_ip = request.client.host if request.client else "unknown"
    port = os.environ.get("TRANSACTION_PORT", 8081)
    source = f"transaction_service:{port}{request.url.path}"
    
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "destination": client_ip,
        "status_code": status_code,
        "headers": {"content-type": "application/json"}
    }
    
    if body is not None:
        log_data["body"] = body
        
    logger.info(f"Response: {json.dumps(log_data, cls=DateTimeEncoder)}")

# Custom response class that logs the response
class LoggingJSONResponse(JSONResponse):
    def __init__(self, content, status_code=200, request=None, **kwargs):
        super().__init__(content=content, status_code=status_code, **kwargs)
        if request:
            log_response_info(request, status_code, content)

# Middleware for request/response logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log request without reading the body
    log_request_info(request)
    
    # Process the request
    response = await call_next(request)
    
    # Note: We don't log response here because individual endpoints will use LoggingJSONResponse
    return response

# Transaction endpoints
@app.post("/api/transactions", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    try:
        # Log the incoming transaction data
        log_request_info(request, transaction.dict())
        
        # Create transaction object with current timestamp if not provided
        db_transaction = TransactionModel(
            customer=transaction.customer,
            timestamp=transaction.timestamp or datetime.utcnow(),
            status=TransactionStatus.SUBMITTED,  # Always start with submitted status
            vendor_id=transaction.vendor_id,
            amount=transaction.amount
        )
        
        # Save to database
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        # Convert SQLAlchemy model to dict for proper serialization
        transaction_dict = {
            "id": db_transaction.id,
            "customer": db_transaction.customer,
            "timestamp": db_transaction.timestamp.isoformat() if db_transaction.timestamp else None,
            "status": db_transaction.status,
            "vendor_id": db_transaction.vendor_id,
            "amount": float(db_transaction.amount)
        }
        
        logger.info(f"Transaction created: ID={db_transaction.id}, Customer={transaction.customer}")
        return LoggingJSONResponse(content=transaction_dict, status_code=status.HTTP_201_CREATED, request=request)
    except Exception as e:
        # Log detailed error for debugging
        logger.error(f"Error creating transaction: {str(e)}")
        error_response = {"detail": f"Failed to create transaction: {str(e)}"}
        log_response_info(request, status.HTTP_500_INTERNAL_SERVER_ERROR, error_response)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )

@app.get("/api/transactions", response_model=List[Transaction])
async def read_transactions(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: Optional[TransactionStatus] = None,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    query = db.query(TransactionModel)
    
    # Apply status filter if provided
    if status:
        query = query.filter(TransactionModel.status == status)
    
    db_transactions = query.offset(skip).limit(limit).all()
    
    # Convert SQLAlchemy models to dicts for proper serialization
    transactions = []
    for db_transaction in db_transactions:
        transactions.append({
            "id": db_transaction.id,
            "customer": db_transaction.customer,
            "timestamp": db_transaction.timestamp.isoformat() if db_transaction.timestamp else None,
            "status": db_transaction.status,
            "vendor_id": db_transaction.vendor_id,
            "amount": float(db_transaction.amount)
        })
    
    logger.info(f"Retrieved {len(transactions)} transactions")
    return LoggingJSONResponse(content=transactions, request=request)

@app.get("/api/transactions/{transaction_id}", response_model=TransactionInDB)
async def read_transaction(
    transaction_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    
    if transaction is None:
        logger.warning(f"Transaction not found: ID={transaction_id}")
        error_response = {"detail": "Transaction not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get the latest prediction for this transaction if it exists
    result = db.query(ResultModel).filter(
        ResultModel.transaction_id == transaction_id
    ).order_by(ResultModel.timestamp.desc()).first()
    
    transaction_dict = {
        "id": transaction.id,
        "customer": transaction.customer,
        "timestamp": transaction.timestamp.isoformat() if transaction.timestamp else None,
        "status": transaction.status,
        "vendor_id": transaction.vendor_id,
        "amount": float(transaction.amount)
    }
    
    # Add prediction data if available
    if result:
        transaction_dict["is_fraudulent"] = result.is_fraud
        transaction_dict["confidence"] = float(result.confidence)
    
    logger.info(f"Retrieved transaction: ID={transaction_id}")
    return LoggingJSONResponse(content=transaction_dict, request=request)

@app.put("/api/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    status: TransactionStatus,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Log the update request
    log_request_info(request, {"transaction_id": transaction_id, "status": status})
    
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    
    if transaction is None:
        logger.warning(f"Transaction not found for update: ID={transaction_id}")
        error_response = {"detail": "Transaction not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update status
    transaction.status = status
    db.commit()
    db.refresh(transaction)
    
    # Convert SQLAlchemy model to dict for proper serialization
    transaction_dict = {
        "id": transaction.id,
        "customer": transaction.customer,
        "timestamp": transaction.timestamp.isoformat() if transaction.timestamp else None,
        "status": transaction.status,
        "vendor_id": transaction.vendor_id,
        "amount": float(transaction.amount)
    }
    
    logger.info(f"Updated transaction status: ID={transaction_id}, Status={status}")
    return LoggingJSONResponse(content=transaction_dict, request=request)

# Prediction endpoints (ML results)
@app.post("/api/transactions/{transaction_id}/results", response_model=Prediction, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    transaction_id: int,
    prediction: PredictionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Log the prediction data
    log_request_info(request, prediction.dict())
    
    # Check if transaction exists
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for prediction: ID={transaction_id}")
        error_response = {"detail": "Transaction not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Create result object
    db_result = ResultModel(
        transaction_id=transaction_id,
        is_fraud=prediction.is_fraudulent,
        confidence=prediction.confidence,
        timestamp=datetime.utcnow()
    )
    
    # Save to database
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    # Convert to response model
    result_dict = {
        "id": db_result.id,
        "transaction_id": db_result.transaction_id,
        "is_fraudulent": db_result.is_fraud,
        "confidence": float(db_result.confidence),
        "timestamp": db_result.timestamp.isoformat() if db_result.timestamp else None
    }
    
    logger.info(f"Prediction created: ID={db_result.id}, Transaction ID={transaction_id}")
    return LoggingJSONResponse(content=result_dict, status_code=status.HTTP_201_CREATED, request=request)

@app.get("/api/transactions/{transaction_id}/results", response_model=List[Prediction])
async def read_transaction_results(
    transaction_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Check if transaction exists
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for results retrieval: ID={transaction_id}")
        error_response = {"detail": "Transaction not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get all results for the transaction
    results = db.query(ResultModel).filter(
        ResultModel.transaction_id == transaction_id
    ).order_by(ResultModel.timestamp.desc()).all()
    
    # Convert to response model
    results_list = []
    for result in results:
        results_list.append({
            "id": result.id,
            "transaction_id": result.transaction_id,
            "is_fraudulent": result.is_fraud,
            "confidence": float(result.confidence),
            "timestamp": result.timestamp.isoformat() if result.timestamp else None
        })
    
    logger.info(f"Retrieved {len(results)} predictions for transaction: ID={transaction_id}")
    return LoggingJSONResponse(content=results_list, request=request)

if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or use default 8081
    port = int(os.environ.get("TRANSACTION_PORT", 8081))
    print(f"Starting Transaction Service on port {port}")
    uvicorn.run("app.main:app", host="localhost", port=port, reload=True)