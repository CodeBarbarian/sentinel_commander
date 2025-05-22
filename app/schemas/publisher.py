# app/schemas/publisher.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PublisherEntryCreate(BaseModel):
    value: str
    comment: Optional[str] = None

class PublisherEntryOut(PublisherEntryCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PublisherListCreate(BaseModel):
    name: str
    description: Optional[str] = None

class PublisherListOut(PublisherListCreate):
    id: int
    guid: str
    created_at: datetime
    entries: List[PublisherEntryOut] = []

    model_config = ConfigDict(from_attributes=True)

class PublisherEntryAPIAdd(BaseModel):
    guid: str
    value: str
    comment: Optional[str] = None

class PublisherEntryAPIDelete(BaseModel):
    guid: str
    value: str