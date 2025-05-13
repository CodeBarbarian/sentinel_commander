from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Playbook(Base):
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    steps = Column(Text, nullable=True)  # Can be markdown or structured JSON

    classification = Column(String, nullable=True)  # e.g., "Incident Response", "Forensics"
    created_by = Column(Integer, nullable=True)     # Can link to user model if desired
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    cases = relationship("CasePlaybook", back_populates="playbook", cascade="all, delete-orphan")
