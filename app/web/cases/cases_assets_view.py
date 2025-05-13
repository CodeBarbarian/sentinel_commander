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

@router.post("/cases/{case_id}/assets/link")
def link_asset_to_case(case_id: int, asset_id: int = Form(...), db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not case or not asset:
        raise HTTPException(status_code=404, detail="Case or Asset not found")

    if asset not in case.assets:
        case.assets.append(asset)
        db.commit()

        log_timeline_event(
            db=db,
            case_id=case_id,
            event_type="asset_linked",
            message=f"Asset '{asset.name}' linked to case.",
        )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#assets", status_code=303)

@router.post("/cases/{case_id}/assets/new")
def create_and_link_asset(
    case_id: int,
    name: str = Form(...),
    ip_address: str = Form(""),
    hostname: str = Form(""),
    type: str = Form(""),
    owner: str = Form(""),
    tags: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    asset = Asset(
        name=name,
        ip_address=ip_address,
        hostname=hostname,
        type=type,
        owner=owner,
        tags=tags,
        notes=notes,
    )
    db.add(asset)
    db.commit()

    case.assets.append(asset)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="asset_created_and_linked",
        message=f"Created and linked new asset '{name}'."
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#assets", status_code=303)

@router.post("/cases/{case_id}/assets/{asset_id}/unlink")
def unlink_asset_from_case(case_id: int, asset_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    asset = db.query(Asset).filter(Asset.id == asset_id).first()

    if not case or not asset:
        raise HTTPException(status_code=404, detail="Case or Asset not found")

    if asset in case.assets:
        case.assets.remove(asset)
        db.commit()

        log_timeline_event(
            db=db,
            case_id=case_id,
            event_type="asset_unlinked",
            message=f"Asset '{asset.name}' unlinked from case.",
        )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#assets", status_code=303)