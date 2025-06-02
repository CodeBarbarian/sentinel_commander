from pydantic import BaseModel, HttpUrl, ConfigDict
from typing import Optional

class ModuleCreate(BaseModel):
    name: str
    is_local: bool
    local_key: Optional[str] = None
    remote_url: Optional[HttpUrl] = None
    remote_api_key: Optional[str] = None

class ModuleUpdate(ModuleCreate):
    id: int

class ModuleOut(ModuleCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)