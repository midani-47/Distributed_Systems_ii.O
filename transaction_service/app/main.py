import os
import uuid
import json
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.models import Transaction, TransactionCreate, TransactionInDB, Prediction, PredictionCreate, TransactionStatus
from app.database import get_db, create_tables, TransactionModel, ResultModel
from app.auth import verify_token, require_role
from app.logger import get_logger, RequestResponseFilter

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Create and configure the application
app = FastAPI(
    title="Transaction Service",
    description="Service for managing financial transactions and fraud predictions",
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
logger = get_logger("transaction_service", "transaction_service.log")

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()
    logger.info("Transaction Service started and database initialized")

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
        "destination": f"transaction_service:{port}{request.url.path}",
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

# Transaction endpoints
@app.post("/api/transactions", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Create transaction object
    db_transaction = TransactionModel(
        customer=transaction.customer,
        timestamp=transaction.timestamp,
        status=TransactionStatus.SUBMITTED,  # Always start with submitted status
        vendor_id=transaction.vendor_id,
        amount=transaction.amount
    )
    
    # Save to database
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    logger.info(f"Transaction created: ID={db_transaction.id}, Customer={transaction.customer}")
    return db_transaction

# New endpoint with simpler URL structure
@app.get("/transactions", response_model=List[Transaction])
async def read_transactions_simple(
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
    
    transactions = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(transactions)} transactions")
    return transactions

@app.get("/api/transactions", response_model=List[Transaction])
async def read_transactions(
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
    
    transactions = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(transactions)} transactions")
    return transactions

@app.get("/api/transactions/{transaction_id}", response_model=TransactionInDB)
async def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    user_data: dict = Depends(verify_token)
):
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    
    if transaction is None:
        logger.warning(f"Transaction not found: ID={transaction_id}")
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get the latest prediction for this transaction if it exists
    result = db.query(ResultModel).filter(
        ResultModel.transaction_id == transaction_id
    ).order_by(ResultModel.timestamp.desc()).first()
    
    transaction_dict = {
        "id": transaction.id,
        "customer": transaction.customer,
        "timestamp": transaction.timestamp,
        "status": transaction.status,
        "vendor_id": transaction.vendor_id,
        "amount": transaction.amount
    }
    
    # Add prediction data if available
    if result:
        transaction_dict["is_fraudulent"] = result.is_fraud
        transaction_dict["confidence"] = result.confidence
    
    logger.info(f"Retrieved transaction: ID={transaction_id}")
    return transaction_dict

@app.put("/api/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction(
    transaction_id: int,
    status: TransactionStatus,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    
    if transaction is None:
        logger.warning(f"Transaction not found for update: ID={transaction_id}")
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update status
    transaction.status = status
    db.commit()
    db.refresh(transaction)
    
    logger.info(f"Updated transaction status: ID={transaction_id}, Status={status}")
    return transaction

# Prediction endpoints (ML results)
@app.post("/api/transactions/{transaction_id}/results", response_model=Prediction, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    transaction_id: int,
    prediction: PredictionCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Check if transaction exists
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for prediction: ID={transaction_id}")
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Create result object
    db_result = ResultModel(
        transaction_id=transaction_id,
        is_fraud=prediction.is_fraudulent,
        confidence=prediction.confidence
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
        "confidence": db_result.confidence,
        "timestamp": db_result.timestamp
    }
    
    logger.info(f"Prediction created: ID={db_result.id}, Transaction ID={transaction_id}")
    return result_dict

@app.get("/api/transactions/{transaction_id}/results", response_model=List[Prediction])
async def read_transaction_results(
    transaction_id: int,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Check if transaction exists
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for results retrieval: ID={transaction_id}")
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
            "confidence": result.confidence,
            "timestamp": result.timestamp
        })
    
    logger.info(f"Retrieved {len(results)} predictions for transaction: ID={transaction_id}")
    return results_list

if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or use default 8081
    port = int(os.environ.get("TRANSACTION_PORT", 8081))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True) 