from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class PlaybookBase(BaseModel):
    name: str
    description: Optional[str] = None
    steps: Optional[str] = None  # Markdown or structured JSON
    classification: Optional[str] = None

class PlaybookCreate(PlaybookBase):
    pass

class PlaybookUpdate(PlaybookBase):
    pass

class PlaybookOut(PlaybookBase):
    id: int
    name: str
    description: Optional[str]
    classification: Optional[str]
    steps: Optional[str]
    created_at: datetime
    updated_at: datetime
    rendered_steps: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
