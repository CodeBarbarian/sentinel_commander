from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base

class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    query_string = Column(String(2048), nullable=False)
    created_at = Column(DateTime, default=func.now())
