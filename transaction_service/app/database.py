from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
from datetime import datetime
from app.models import TransactionStatus

# Create database file path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'transactions.db')}"

# Create SQLAlchemy engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for ORM models
Base = declarative_base()

# Define SQLAlchemy ORM models
class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.SUBMITTED)
    vendor_id = Column(String, index=True)
    amount = Column(Float)
    
    predictions = relationship("PredictionModel", back_populates="transaction")


class PredictionModel(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    is_fraudulent = Column(Boolean)
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("TransactionModel", back_populates="predictions")


# Create database tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 