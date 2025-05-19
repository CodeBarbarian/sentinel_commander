# app/schemas/ioc.py

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

# Shared base model
class IOCBase(BaseModel):
    type: str
    value: str
    description: Optional[str] = None
    source: Optional[str] = None
    tags: Optional[str] = None

# For creating new IOCs
class IOCCreate(IOCBase):
    pass

# For updating existing IOCs
class IOCUpdate(IOCBase):
    pass

# For reading/output
class IOCOut(IOCBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
