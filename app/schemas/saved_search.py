from pydantic import BaseModel, ConfigDict
from datetime import datetime

class SavedSearchOut(BaseModel):
    id: int
    name: str
    query_string: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)