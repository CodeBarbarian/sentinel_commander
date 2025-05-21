# app/models/publisher.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class PublisherList(Base):
    __tablename__ = "publisher_lists"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    guid = Column(String(64), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    list_type = Column(String(50), nullable=False)
    entries = relationship("PublisherEntry", back_populates="list", cascade="all, delete-orphan")


class PublisherEntry(Base):
    __tablename__ = "publisher_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    list_id = Column(Integer, ForeignKey("publisher_lists.id", ondelete="CASCADE"))
    value = Column(Text, nullable=False)
    comment = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    list = relationship("PublisherList", back_populates="entries")