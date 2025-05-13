# app/models/case_ioc.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class CaseIOC(Base):
    __tablename__ = "case_iocs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    type = Column(String(50), nullable=False)  # e.g. 'ip', 'domain', 'hash', 'email'
    value = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)  # Analyst, MISP, External Tool, etc.
    tags = Column(String(255), nullable=True)  # Comma-separated or JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="iocs")
