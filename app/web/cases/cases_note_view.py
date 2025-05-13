from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.models.assets import Asset
from app.models.case import Case
from app.models.customer import Customer
from app.models.user import User
from app.models.case_tag import CaseTag
from app.models.case_note import CaseNote
from app.models.case_tasks import CaseTask
from app.schemas.assets import AssetOut
from app.schemas.case_note import CaseNoteOut
from app.schemas.case_tasks import CaseTaskOut
from app.models.case_ioc import CaseIOC
from app.schemas.case_ioc import CaseIOCOut
from fastapi.templating import Jinja2Templates
from typing import Optional
from fastapi import UploadFile, File
from app.models.case_evidence import CaseEvidence
from app.models.case_timeline import CaseTimelineEvent
from app.schemas.case_evidence import CaseEvidenceOut
from app.schemas.case_timeline import CaseTimelineOut
from app.models.alert import Alert
from app.models.case_playbooks import CasePlaybook
from app.models.playbooks import Playbook
from app.schemas.playbooks import PlaybookOut
import markdown
from app.utils import auth
import shutil
import os
from datetime import datetime
import uuid
from werkzeug.utils import secure_filename

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def parse_optional_int(value: str) -> Optional[int]:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

def log_timeline_event(
    db: Session,
    case_id: int,
    event_type: str,
    message: str,
    actor_id: Optional[int] = None,
    details: Optional[str] = None
):
    timeline_entry = CaseTimelineEvent(
        case_id=case_id,
        actor_id=actor_id,
        event_type=event_type,
        message=message,
        details=details,
    )
    db.add(timeline_entry)
    db.commit()

@router.post("/cases/{case_id}/notes")
def add_note_to_case(
    case_id: int,
    request: Request,
    content: str = Form(...),
    author_id: int = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    note = CaseNote(case_id=case_id, author_id=author_id, content=content)
    db.add(note)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="note_added",
        message="Note added to case.",
        actor_id=author_id,
        details=content[:255]  # Limit for preview in timeline
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#notes", status_code=303)

@router.post("/cases/{case_id}/notes/{note_id}/edit")
def edit_note(
    case_id: int,
    note_id: int,
    content: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    note = db.query(CaseNote).filter(CaseNote.id == note_id, CaseNote.case_id == case_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.content = content
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="note_edited",
        message=f"Note ID {note_id} was edited.",
        actor_id=note.author_id,
        details=content[:255]  # Limit the length for timeline readability
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#notes", status_code=303)

@router.post("/cases/{case_id}/notes/{note_id}/delete")
def delete_note(
    case_id: int,
    note_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    note = db.query(CaseNote).filter(CaseNote.id == note_id, CaseNote.case_id == case_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    author_id = note.author_id
    note_preview = note.content[:255]

    db.delete(note)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="note_deleted",
        message=f"Note ID {note_id} was deleted.",
        actor_id=author_id,
        details=note_preview
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#notes", status_code=303)