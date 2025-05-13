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


@router.post("/cases/{case_id}/evidence")
def upload_evidence_to_case(
    case_id: int,
    title: str = Form(...),
    description: str = Form(""),
    type: str = Form(""),
    tags: str = Form(""),
    uploaded_by: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Create upload directory if it doesn't exist
    upload_dir = f"app/static/uploads/evidence/{case_id}"
    os.makedirs(upload_dir, exist_ok=True)

    # Generate a secure, random filename
    file_ext = os.path.splitext(file.filename)[1]
    random_name = f"{uuid.uuid4().hex}{file_ext}"
    secure_name = secure_filename(random_name)
    file_path = os.path.join(upload_dir, secure_name)

    # Save the uploaded file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    # Create evidence record in the database
    evidence = CaseEvidence(
        case_id=case_id,
        uploaded_by=uploaded_by,
        title=title,
        description=description,
        type=type,
        tags=tags,
        filename=f"{case_id}/{secure_name}"
    )
    db.add(evidence)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="evidence_uploaded",
        message=f"Evidence uploaded: '{title}'",
        actor_id=uploaded_by,
        details=description[:255] if description else None
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#evidence", status_code=303)

@router.post("/cases/{case_id}/evidence/{evidence_id}/delete")
def delete_evidence(
    case_id: int,
    evidence_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    evidence = db.query(CaseEvidence).filter(CaseEvidence.id == evidence_id, CaseEvidence.case_id == case_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")

    deleted_title = evidence.title
    deleted_filename = evidence.filename
    deleted_by = evidence.uploaded_by

    # Try deleting the physical file
    try:
        os.remove(f"app/static/uploads/evidence/{deleted_filename}")
    except FileNotFoundError:
        pass

    db.delete(evidence)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="evidence_deleted",
        message=f"Evidence deleted: '{deleted_title}'",
        actor_id=deleted_by,
        details=f"Deleted file: {deleted_filename}"
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#evidence", status_code=303)