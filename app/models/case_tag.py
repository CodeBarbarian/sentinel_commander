from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base
from sqlalchemy.orm import relationship

# models/case_tag.py
class CaseTag(Base):
    __tablename__ = "case_tags"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    tag = Column(String, nullable=False)

    case = relationship("Case", back_populates="tags")
