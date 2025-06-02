from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    is_local = Column(Boolean, default=True)
    local_key = Column(String(200), nullable=True)      # Used if local
    remote_url = Column(String(255), nullable=True)     # Used if remote
    remote_api_key = Column(String(255), nullable=True) # Used if remote