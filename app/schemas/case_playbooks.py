from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CasePlaybookBase(BaseModel):
    case_id: int
    playbook_id: int

class CasePlaybookCreate(CasePlaybookBase):
    pass

class CasePlaybookOut(CasePlaybookBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)