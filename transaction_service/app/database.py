from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.orm import declarative_base
import os
from datetime import datetime
from app.models import TransactionStatus

# figure out where to put the db file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'transactions.db')}"

# setup the sql engine thingy, check_same_thread cuz sqlite is weird
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# this is for making the models work with orm
Base = declarative_base()

# these are the database tables as classes
class TransactionModel(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.SUBMITTED)
    vendor_id = Column(String, index=True)
    amount = Column(Float)
    
    # connection to the results table
    results = relationship("ResultModel", back_populates="transaction")


class ResultModel(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_fraud = Column(Boolean)
    confidence = Column(Float)
    
    # link back to transaction
    transaction = relationship("TransactionModel", back_populates="results")


# run this at startup to create tables if they dont exist
def create_tables():
    Base.metadata.create_all(bind=engine)


# this gives a database session and closes it automatically afterwards
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 