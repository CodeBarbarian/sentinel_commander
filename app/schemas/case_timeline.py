from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from pydantic import ConfigDict

class CaseTimelineBase(BaseModel):
    event_type: str = Field(..., example="note_added")
    message: str = Field(..., example="Note added by Alice")
    details: Optional[str] = Field(None, example="Note ID: 42")

class CaseTimelineCreate(CaseTimelineBase):
    actor_id: Optional[int] = Field(None, example=1)

class CaseTimelineOut(CaseTimelineBase):
    id: int
    case_id: int
    actor_id: Optional[int]
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)