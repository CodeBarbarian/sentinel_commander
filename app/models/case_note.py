# app/models/case_note.py
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class CaseNote(Base):
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="notes")
    author = relationship("User")
