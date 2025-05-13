import uuid
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    guid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    api_key = Column(String, unique=True, index=True)
    name = Column(String, unique=True, nullable=False)         # e.g., "wazuh_manager_1"
    display_name = Column(String, nullable=True)               # e.g., "Wazuh Manager 1"
    is_active = Column(Boolean, default=True)
    parser_config = Column(String, nullable=True)              # For YAML/JSON parser later
    is_protected = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
