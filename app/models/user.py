from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"  # <-- This is what SQLAlchemy relies on

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(150), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, nullable=True)

    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="analyst")
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
