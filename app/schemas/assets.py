from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class AssetBase(BaseModel):
    name: str
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    type: Optional[str] = None
    owner: Optional[str] = None
    tags: Optional[str] = None
    notes: Optional[str] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(AssetBase):
    pass

class AssetOut(AssetBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
