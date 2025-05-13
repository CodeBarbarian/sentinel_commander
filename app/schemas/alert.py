from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime

class AlertCreate(BaseModel):
    source: str
    source_ref_id: Optional[str] = None
    severity: int
    message: str
    observables: Optional[str] = None
    status: Optional[str] = Field(default="new")
    resolution: Optional[str] = None
    resolution_comment: Optional[str] = None
    tags: Optional[str] = ""
    source_event_time: Optional[datetime] = None
    source_payload: Optional[str] = None

class AlertUpdate(BaseModel):
    message: Optional[str] = None
    observables: Optional[str] = None
    severity: Optional[int] = None
    status: Optional[str] = None
    resolution: Optional[str] = None
    resolution_comment: Optional[str] = None
    tags: Optional[str] = None

class AlertOut(BaseModel):
    id: int
    source: str
    source_ref_id: Optional[str]
    severity: int
    message: str
    observables: Optional[str]
    status: str
    resolution: Optional[str]
    resolution_comment: Optional[str]
    tags: Optional[str]
    source_event_time: Optional[datetime]
    source_payload: Optional[str]
    created_at: datetime
    source_id: Optional[int]
    source_display_name: Optional[str]
    parsed_fields: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class AlertBulkActionRequest(BaseModel):
    action: Literal["update", "delete"]
    alert_ids: List[int]
    fields: Optional[Dict[str, Any]] = None
