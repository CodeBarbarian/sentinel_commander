# app/schemas/alert_enrichment.py

from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class AlertEnrichmentBase(BaseModel):
    enrichment_type: str
    source: Optional[str] = None
    data: Dict[str, Any]
    notes: Optional[str] = None

class AlertEnrichmentCreate(AlertEnrichmentBase):
    alert_id: int

class AlertEnrichmentOut(AlertEnrichmentBase):
    id: int
    alert_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)