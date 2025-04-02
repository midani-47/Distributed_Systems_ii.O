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
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: TransactionStatus = TransactionStatus.SUBMITTED
    vendor_id: str
    amount: float


class TransactionCreate(TransactionBase):
    pass


class Transaction(TransactionBase):
    id: int
    
    class Config:
        orm_mode = True


class TransactionInDB(Transaction):
    is_fraudulent: Optional[bool] = None
    confidence: Optional[float] = None


class PredictionCreate(BaseModel):
    transaction_id: int
    is_fraudulent: bool
    confidence: float


class Prediction(PredictionCreate):
    id: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True 