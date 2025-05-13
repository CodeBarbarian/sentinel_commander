from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import engine, Base, get_db

class CaseTask(Base):
    __tablename__ = "case_tasks"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="open")  # open / in_progress / done
    assigned_to = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    case = relationship("Case", back_populates="tasks")
    assignee = relationship("User")