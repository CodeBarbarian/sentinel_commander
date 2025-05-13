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


@router.post("/cases/{case_id}/alerts/link")
def link_alert_to_case(case_id: int, alert_id: int = Form(...), db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.case_id = case_id
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="alert_linked",
        message=f"Alert {alert.id} linked to this case.",
        details=alert.message[:255] if alert.message else None
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#alerts", status_code=303)

@router.post("/cases/{case_id}/alerts/{alert_id}/unlink")
def unlink_alert_from_case(case_id: int, alert_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.case_id == case_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.case_id = None
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="alert_unlinked",
        message=f"Alert {alert.id} unlinked from this case.",
        details=alert.message[:255] if alert.message else None
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#alerts", status_code=303)
