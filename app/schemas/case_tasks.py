from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CaseTaskCreate(BaseModel):
    title: str
    description: Optional[str]
    status: Optional[str] = "open"
    assigned_to: Optional[int]

class CaseTaskUpdate(BaseModel):
    title: Optional[str]
    description: Optional[str]
    status: Optional[str]
    assigned_to: Optional[int]

class CaseTaskOut(BaseModel):
    id: int
    case_id: int
    title: str
    description: Optional[str]
    status: str
    assigned_to: Optional[int]
    created_at: datetime
    updated_at: datetime
    assignee_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_assignee(cls, obj):
        data = cls.model_validate(obj)
        data.assignee_name = obj.assignee.username if obj.assignee else None
        return data
