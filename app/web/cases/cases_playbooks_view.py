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



@router.post("/cases/{case_id}/playbooks/link")
def link_playbook_to_case(case_id: int, playbook_id: int = Form(...), db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()

    if not case or not playbook:
        raise HTTPException(status_code=404, detail="Case or Playbook not found")

    # Avoid duplicates
    existing_link = (
        db.query(CasePlaybook)
        .filter(CasePlaybook.case_id == case_id, CasePlaybook.playbook_id == playbook_id)
        .first()
    )
    if not existing_link:
        link = CasePlaybook(case_id=case_id, playbook_id=playbook_id)
        db.add(link)
        db.commit()

        log_timeline_event(
            db=db,
            case_id=case_id,
            event_type="playbook_linked",
            message=f"Playbook '{playbook.name}' linked to case."
        )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#playbooks", status_code=303)

@router.post("/cases/{case_id}/playbooks/{playbook_id}/unlink")
def unlink_playbook_from_case(case_id: int, playbook_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    link = (
        db.query(CasePlaybook)
        .filter(CasePlaybook.case_id == case_id, CasePlaybook.playbook_id == playbook_id)
        .first()
    )
    if not link:
        raise HTTPException(status_code=404, detail="Playbook not linked to case")

    db.delete(link)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="playbook_unlinked",
        message=f"Playbook ID {playbook_id} unlinked from case."
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#playbooks", status_code=303)
