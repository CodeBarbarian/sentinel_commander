# app/schemas/case_note.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class CaseNoteCreate(BaseModel):
    case_id: int
    author_id: int
    content: str

class CaseNoteUpdate(BaseModel):
    content: Optional[str]

class CaseNoteOut(BaseModel):
    id: int
    case_id: int
    author_id: int
    content: str
    created_at: datetime
    updated_at: datetime
    author_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_author(cls, note):
        return cls(
            id=note.id,
            case_id=note.case_id,
            author_id=note.author_id,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at,
            author_name=note.author.username if note.author else None
        )

