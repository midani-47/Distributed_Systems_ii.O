import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.models import Transaction, TransactionCreate, TransactionInDB, Prediction, PredictionCreate, TransactionStatus
from app.database import get_db, create_tables, TransactionModel, PredictionModel
from app.auth import verify_token, require_role
from app.logger import get_logger, RequestResponseFilter

# Create logs directory if it doesn't exist
os.makedirs("../../logs", exist_ok=True)

# Create and configure the application
app = FastAPI(
    title="Transaction Service",
    description="Service for managing financial transactions and fraud predictions",
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

# Transaction endpoints
@app.post("/transactions/", response_model=Transaction, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Create transaction object
    db_transaction = TransactionModel(
        customer=transaction.customer,
        timestamp=transaction.timestamp,
        status=transaction.status,
        vendor_id=transaction.vendor_id,
        amount=transaction.amount
    )
    
    # Save to database
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    
    logger.info(f"Transaction created: ID={db_transaction.id}, Customer={transaction.customer}")
    return db_transaction

@app.get("/transactions/", response_model=List[Transaction])
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
    
    # Apply role-based filters
    if user_data["role"] == "secretary":
        # Secretaries can only see customer data
        pass  # No additional filtering needed for transactions themselves
    
    transactions = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(transactions)} transactions")
    return transactions

@app.get("/transactions/{transaction_id}", response_model=TransactionInDB)
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
    prediction = db.query(PredictionModel).filter(
        PredictionModel.transaction_id == transaction_id
    ).order_by(PredictionModel.timestamp.desc()).first()
    
    transaction_dict = {
        "id": transaction.id,
        "customer": transaction.customer,
        "timestamp": transaction.timestamp,
        "status": transaction.status,
        "vendor_id": transaction.vendor_id,
        "amount": transaction.amount
    }
    
    # Add prediction data if available
    if prediction:
        transaction_dict["is_fraudulent"] = prediction.is_fraudulent
        transaction_dict["confidence"] = prediction.confidence
    
    logger.info(f"Retrieved transaction: ID={transaction_id}")
    return transaction_dict

@app.put("/transactions/{transaction_id}", response_model=Transaction)
async def update_transaction_status(
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

# Prediction endpoints
@app.post("/predictions/", response_model=Prediction, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    prediction: PredictionCreate,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Check if transaction exists
    transaction = db.query(TransactionModel).filter(TransactionModel.id == prediction.transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for prediction: ID={prediction.transaction_id}")
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Create prediction object
    db_prediction = PredictionModel(
        transaction_id=prediction.transaction_id,
        is_fraudulent=prediction.is_fraudulent,
        confidence=prediction.confidence
    )
    
    # Save to database
    db.add(db_prediction)
    db.commit()
    db.refresh(db_prediction)
    
    logger.info(f"Prediction created: ID={db_prediction.id}, Transaction ID={prediction.transaction_id}")
    return db_prediction

@app.get("/predictions/transaction/{transaction_id}", response_model=List[Prediction])
async def read_transaction_predictions(
    transaction_id: int,
    db: Session = Depends(get_db),
    user_data: dict = Depends(require_role(["admin", "agent"]))
):
    # Check if transaction exists
    transaction = db.query(TransactionModel).filter(TransactionModel.id == transaction_id).first()
    if not transaction:
        logger.warning(f"Transaction not found for predictions retrieval: ID={transaction_id}")
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get all predictions for the transaction
    predictions = db.query(PredictionModel).filter(
        PredictionModel.transaction_id == transaction_id
    ).order_by(PredictionModel.timestamp.desc()).all()
    
    logger.info(f"Retrieved {len(predictions)} predictions for transaction: ID={transaction_id}")
    return predictions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True) 