from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class CaseEvidence(Base):
    __tablename__ = "case_evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String(50), nullable=True)  # e.g. screenshot, log, document
    filename = Column(String(255), nullable=False)
    tags = Column(String(255), nullable=True)  # Optional comma-separated

    uploaded_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="evidence")
    user = relationship("User")  # uploader
