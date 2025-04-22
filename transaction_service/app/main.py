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
    # attempting to locate modules via standard application import path
    from app.models import Transaction, TransactionCreate, TransactionInDB, Prediction, PredictionCreate, TransactionStatus
    from app.database import get_db, create_tables, TransactionModel, ResultModel
    from app.auth import verify_token, require_role
    from app.logger import get_logger
except ImportError:
    # falling back to direct imports when running as a standalone script
    from models import Transaction, TransactionCreate, TransactionInDB, Prediction, PredictionCreate, TransactionStatus
    from database import get_db, create_tables, TransactionModel, ResultModel
    from auth import verify_token, require_role
    from logger import get_logger

# ensuring logs directory exists for service operation
os.makedirs("logs", exist_ok=True)

# initializing dedicated logger for the transaction service
logger = get_logger("transaction_service", "transaction_service.log")

# custom JSON encoder for proper datetime serialization in logs
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# managing application lifecycle events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # performing startup initialization: setting up database schema
    create_tables()
    logger.info("Transaction Service started and database initialized")
    yield
    # handling graceful shutdown procedures
    logger.info("Transaction Service shutting down")

# configuring the FastAPI application with metadata
app = FastAPI(
    title="Transaction Service",
    description="Service for managing financial transactions and fraud predictions",
    version="1.0.0",
    docs_url="/docs",
    lifespan=lifespan
)

# setting up Cross-Origin Resource Sharing for API accessibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# function for structured request logging
def log_request_info(request: Request, body=None):
    """Capturing comprehensive request details including optional body content"""
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

# function for structured response logging
def log_response_info(request: Request, status_code: int, body=None):
    """Recording structured response data for monitoring and audit trails"""
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

# enhanced JSON response class with integrated logging capability
class LoggingJSONResponse(JSONResponse):
    def __init__(self, content, status_code=200, request=None, **kwargs):
        super().__init__(content=content, status_code=status_code, **kwargs)
        if request:
            log_response_info(request, status_code, content)

# global middleware for consistent request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # capturing initial request metadata before processing
    log_request_info(request)
    
    # passing request through the middleware chain for processing
    response = await call_next(request)
    
    # individual endpoints handle response logging via LoggingJSONResponse
    return response

# API endpoint for creating new transaction records
@app.post("/api/transactions", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    try:
        # logging transaction creation request for auditing
        log_request_info(request, transaction.dict())
        
        # preparing new transaction record with default status
        db_transaction = TransactionModel(
            customer=transaction.customer,
            timestamp=transaction.timestamp or datetime.utcnow(),
            status=TransactionStatus.SUBMITTED,  # initial default status
            vendor_id=transaction.vendor_id,
            amount=transaction.amount
        )
        
        # storing transaction in the database
        db.add(db_transaction)
        db.commit()
        db.refresh(db_transaction)
        
        # formatting database model for API response
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
        # providing comprehensive error handling with logging
        logger.error(f"Error creating transaction: {str(e)}")
        error_response = {"detail": f"Failed to create transaction: {str(e)}"}
        log_response_info(request, status.HTTP_500_INTERNAL_SERVER_ERROR, error_response)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create transaction: {str(e)}"
        )

# API endpoint for retrieving transaction listings with filtering options
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
    
    # applying optional status filtering when specified
    if status:
        query = query.filter(TransactionModel.status == status)
    
    db_transactions = query.offset(skip).limit(limit).all()
    
    # transforming database results into API response format
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

# API endpoint for accessing detailed transaction information with prediction data
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
    
    # including the most recent fraud detection result when available
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
    
    # enriching response with fraud analysis when present
    if result:
        transaction_dict["is_fraudulent"] = result.is_fraud
        transaction_dict["confidence"] = float(result.confidence)
    
    logger.info(f"Retrieved transaction: ID={transaction_id}")
    return LoggingJSONResponse(content=transaction_dict, request=request)

# API endpoint for updating transaction status
@app.put("/api/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    status: TransactionStatus,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # recording status update request for audit trails
    log_request_info(request, {"transaction_id": transaction_id, "status": status})
    
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    
    if transaction is None:
        logger.warning(f"Transaction not found for update: ID={transaction_id}")
        error_response = {"detail": "Transaction not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # modifying transaction status in the database
    transaction.status = status
    db.commit()
    db.refresh(transaction)
    
    # formatting updated record for API response
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

# API endpoint for recording fraud detection results
@app.post("/api/transactions/{transaction_id}/results", response_model=Prediction, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    transaction_id: int,
    prediction: PredictionCreate,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # logging prediction submission for auditing
    log_request_info(request, prediction.dict())
    
    # verifying the referenced transaction exists
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for prediction: ID={transaction_id}")
        error_response = {"detail": "Transaction not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # preparing fraud analysis result record
    db_result = ResultModel(
        transaction_id=transaction_id,
        is_fraud=prediction.is_fraudulent,
        confidence=prediction.confidence,
        timestamp=datetime.utcnow()
    )
    
    # storing prediction in the database
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    
    # formatting database model for API response
    result_dict = {
        "id": db_result.id,
        "transaction_id": db_result.transaction_id,
        "is_fraudulent": db_result.is_fraud,
        "confidence": float(db_result.confidence),
        "timestamp": db_result.timestamp.isoformat() if db_result.timestamp else None
    }
    
    logger.info(f"Prediction created: ID={db_result.id}, Transaction ID={transaction_id}")
    return LoggingJSONResponse(content=result_dict, status_code=status.HTTP_201_CREATED, request=request)

# API endpoint for accessing historical fraud predictions
@app.get("/api/transactions/{transaction_id}/results", response_model=List[Prediction])
async def read_transaction_results(
    transaction_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # confirming transaction exists before retrieving results
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for results retrieval: ID={transaction_id}")
        error_response = {"detail": "Transaction not found"}
        log_response_info(request, status.HTTP_404_NOT_FOUND, error_response)
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # retrieving all historical predictions in chronological order
    results = db.query(ResultModel).filter(
        ResultModel.transaction_id == transaction_id
    ).order_by(ResultModel.timestamp.desc()).all()
    
    # transforming database records into API response format
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

# service entry point for direct script execution
if __name__ == "__main__":
    import uvicorn
    # determining operational port from environment configuration
    port = int(os.environ.get("TRANSACTION_PORT", 8081))
    print(f"Starting Transaction Service on port {port}")
    uvicorn.run("app.main:app", host="localhost", port=port, reload=True)