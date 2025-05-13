from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional

class SourceCreate(BaseModel):
    name: str
    display_name: str

class SourceUpdate(BaseModel):
    name: Optional[str] = None
    display_name: Optional[str] = None
    is_active: Optional[bool] = None
    parser_config: Optional[str] = None

class SourceOut(BaseModel):
    id: int
    guid: str
    name: str
    display_name: str
    is_active: bool
    is_protected: bool
    api_key: str
    created_at: datetime
    parser_config: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# Optional: public version for UI display
class SourcePublic(BaseModel):
    id: int
    guid: str
    display_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
