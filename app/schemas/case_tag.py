from pydantic import BaseModel, ConfigDict

class CaseTagOut(BaseModel):
    id: int
    tag: str

    model_config = ConfigDict(from_attributes=True)

class CaseTagCreate(BaseModel):
    tag: str