from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import engine, Base, get_db


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)

    contact_name = Column(String(255), nullable=True)
    contact_email = Column(String(255), nullable=True)
    tags = Column(Text, nullable=True)  # Can convert to JSON later if needed

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Future expansion
    # alerts = relationship("Alert", back_populates="customer")
    # users = relationship("User", back_populates="customer")
    sources = relationship("Source", back_populates="customer")
    detail = relationship("CustomerDetail", back_populates="customer", cascade="all, delete", uselist=False)