# app/models/ioc.py

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.core.database import Base

class IOC(Base):
    __tablename__ = "iocs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # ip, domain, hash, etc.
    value = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)  # MISP, Analyst, etc.
    tags = Column(String(255), nullable=True)  # Comma-separated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
