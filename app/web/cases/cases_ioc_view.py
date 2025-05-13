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

    @router.post("/cases/{case_id}/iocs")
    def add_ioc_to_case(
            case_id: int,
            type: str = Form(...),
            value: str = Form(...),
            description: str = Form(""),
            source: str = Form(""),
            tags: str = Form(""),
            db: Session = Depends(get_db),
            user=Depends(auth.get_current_user)
    ):
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        ioc = CaseIOC(
            case_id=case_id,
            type=type,
            value=value,
            description=description,
            source=source,
            tags=tags,
        )
        db.add(ioc)
        db.commit()

        log_timeline_event(
            db=db,
            case_id=case_id,
            event_type="ioc_added",
            message=f"IOC added: [{type}] {value}",
            actor_id=None,
            details=description[:255] if description else None
        )

        return RedirectResponse(url=f"/web/v1/cases/{case_id}#iocs", status_code=303)

    @router.post("/cases/{case_id}/iocs/{ioc_id}/edit")
    def edit_ioc(
            case_id: int,
            ioc_id: int,
            type: str = Form(...),
            value: str = Form(...),
            description: str = Form(""),
            source: str = Form(""),
            tags: str = Form(""),
            db: Session = Depends(get_db),
            user=Depends(auth.get_current_user)
    ):
        ioc = db.query(CaseIOC).filter(CaseIOC.id == ioc_id, CaseIOC.case_id == case_id).first()
        if not ioc:
            raise HTTPException(status_code=404, detail="IOC not found")

        previous_state = {
            "type": ioc.type,
            "value": ioc.value,
            "description": ioc.description,
            "source": ioc.source,
            "tags": ioc.tags,
        }

        ioc.type = type
        ioc.value = value
        ioc.description = description
        ioc.source = source
        ioc.tags = tags

        db.commit()

        # Build change summary
        changes = []
        if previous_state["type"] != type:
            changes.append(f"Type: '{previous_state['type']}' → '{type}'")
        if previous_state["value"] != value:
            changes.append(f"Value updated")
        if previous_state["description"] != description:
            changes.append("Description updated")
        if previous_state["source"] != source:
            changes.append(f"Source: '{previous_state['source']}' → '{source}'")
        if previous_state["tags"] != tags:
            changes.append("Tags updated")

        log_timeline_event(
            db=db,
            case_id=case_id,
            event_type="ioc_edited",
            message=f"IOC '{value}' was edited.",
            actor_id=None,
            details="; ".join(changes) if changes else "No changes detected"
        )

        return RedirectResponse(url=f"/web/v1/cases/{case_id}#iocs", status_code=303)

    @router.post("/cases/{case_id}/iocs/{ioc_id}/delete")
    def delete_ioc(
            case_id: int,
            ioc_id: int,
            db: Session = Depends(get_db),
            user=Depends(auth.get_current_user)
    ):
        ioc = db.query(CaseIOC).filter(CaseIOC.id == ioc_id, CaseIOC.case_id == case_id).first()
        if not ioc:
            raise HTTPException(status_code=404, detail="IOC not found")

        deleted_value = ioc.value
        deleted_type = ioc.type

        db.delete(ioc)
        db.commit()

        log_timeline_event(
            db=db,
            case_id=case_id,
            event_type="ioc_deleted",
            message=f"IOC deleted: [{deleted_type}] {deleted_value}",
            actor_id=None,
            details=None
        )

        return RedirectResponse(url=f"/web/v1/cases/{case_id}#iocs", status_code=303)

