from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import declarative_base
import os
from datetime import datetime
from app.models import TransactionStatus

# determining database file location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'transactions.db')}"

# initializing SQLAlchemy engine with SQLite-specific options
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# creating base class for ORM models
Base = declarative_base()

# defining database schema as ORM models
class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.SUBMITTED)
    vendor_id = Column(String, index=True)
    amount = Column(Float)
    
    # establishing relationship with results table for ORM
    results = relationship("ResultModel", back_populates="transaction")


class ResultModel(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_fraud = Column(Boolean)
    confidence = Column(Float)
    
    # bidirectional relationship with transaction
    transaction = relationship("TransactionModel", back_populates="results")


# creating database tables if they don't exist
def create_tables():
    Base.metadata.create_all(bind=engine)


# dependency for providing database session to endpoints
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 