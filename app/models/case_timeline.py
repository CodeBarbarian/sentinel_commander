from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class CaseTimelineEvent(Base):
    __tablename__ = "case_timeline"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    case = relationship("Case", back_populates="timeline")
