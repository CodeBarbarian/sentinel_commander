from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class CaseEvidenceBase(BaseModel):
    title: str = Field(..., example="Exploit Screenshot")
    description: Optional[str] = Field(None, example="Screenshot of the buffer overflow in action")
    type: Optional[str] = Field(None, example="screenshot")
    tags: Optional[str] = Field(None, example="exploit,proof")
    filename: str = Field(..., example="exploit_screenshot.png")

class CaseEvidenceIn(CaseEvidenceBase):
    uploaded_by: int  # ID of the user uploading

class CaseEvidenceUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    type: Optional[str]
    tags: Optional[str]

class CaseEvidenceOut(CaseEvidenceBase):
    id: int
    case_id: int
    uploaded_by: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
