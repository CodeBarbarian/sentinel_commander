from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import datetime
from app.schemas.case_tag import CaseTagOut

class Case(BaseModel):
    title: str
    description: Optional[str] = None
    classification: Optional[str] = None
    state: Optional[str] = Field(default="new")
    severity: Optional[int] = Field(default=5, ge=0, le=15)
    tags: Optional[List[str]] = Field(default_factory=list)  # Used only on create/update

class CaseCreate(Case):
    customer_id: Optional[int] = None
    assigned_to: Optional[int] = None

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[str] = None
    state: Optional[str] = None
    severity: Optional[int] = None
    tags: Optional[List[str]] = None  # Expect list of strings
    customer_id: Optional[int] = None
    assigned_to: Optional[int] = None

class CaseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    classification: Optional[str]
    state: str
    severity: int
    tags: List[CaseTagOut]
    customer_id: Optional[int]
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CaseOutBrief(BaseModel):
    id: int
    title: str
    state: str
    severity: int
    classification: Optional[str]
    created_at: datetime
    updated_at: datetime
    closing_note: Optional[str]
    closed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
