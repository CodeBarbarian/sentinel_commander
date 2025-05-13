from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from pydantic import ConfigDict

class CaseIOCBase(BaseModel):
    type: str = Field(..., example="ip")
    value: str = Field(..., example="8.8.8.8")
    description: Optional[str] = Field(None, example="Google DNS used in beaconing")
    source: Optional[str] = Field(None, example="Analyst")
    tags: Optional[str] = Field(None, example="C2,External")

class CaseIOCIn(CaseIOCBase):
    pass

class CaseIOCUpdate(BaseModel):
    type: Optional[str]
    value: Optional[str]
    description: Optional[str]
    source: Optional[str]
    tags: Optional[str]

class CaseIOCOut(CaseIOCBase):
    id: int
    case_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
