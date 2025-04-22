from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TransactionStatus(str, Enum):
    SUBMITTED = "submitted"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TransactionBase(BaseModel):
    customer: str
    vendor_id: str
    amount: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int
    status: TransactionStatus = TransactionStatus.SUBMITTED
    
    class Config:
        # gotta make it work with both new n old pydantic versions
        try:
            from_attributes = True
        except ImportError:
            # old version uses orm_mode instead
            orm_mode = True


class TransactionInDB(Transaction):
    is_fraudulent: Optional[bool] = None
    confidence: Optional[float] = None


class PredictionCreate(BaseModel):
    is_fraudulent: bool
    confidence: float


class Prediction(BaseModel):
    id: int
    transaction_id: int
    is_fraudulent: bool
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        # same trick as above for compatibility
        try:
            from_attributes = True
        except ImportError:
            # fallback for old pydantic version
            orm_mode = True 