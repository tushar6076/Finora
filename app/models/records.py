from sqlalchemy import Column, Integer, String, Float, DateTime, Date, Boolean
import datetime
from . import Base

class FinancialRecord(Base):
    __tablename__ = 'records'
    
    id = Column(Integer, primary_key=True)
    person_name = Column(String(100), nullable=False)
    branch_name = Column(String(100))
    amount = Column(Float, default=0.0)
    transaction_date = Column(Date, nullable=False, default=datetime.date.today)
    received_by = Column(String(100))
    transaction_type = Column(String(50))
    transaction_method = Column(String(50))
    
    subject_id = Column(Integer, default=1) 
    chapter_id = Column(Integer, default=1)
    
    # --- New Bin Logic Columns ---
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    # -----------------------------

    created_at = Column(DateTime, default=datetime.datetime.utcnow)