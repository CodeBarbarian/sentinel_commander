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



@router.post("/cases/{case_id}/tasks")
def add_task_to_case(
    case_id: int,
    title: str = Form(...),
    description: str = Form(""),
    assigned_to: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    assigned_to = parse_optional_int(assigned_to)

    task = CaseTask(
        case_id=case_id,
        title=title,
        description=description,
        assigned_to=assigned_to,
    )
    db.add(task)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="task_added",
        message=f"Task added: '{title}'",
        actor_id=assigned_to,
        details=description[:255] if description else None
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#tasks", status_code=303)


@router.post("/cases/{case_id}/tasks/{task_id}/status")
def update_task_status(
    case_id: int,
    task_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    task = db.query(CaseTask).filter(CaseTask.id == task_id, CaseTask.case_id == case_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    previous_status = task.status
    task.status = status
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="task_status_updated",
        message=f"Task '{task.title}' status changed from '{previous_status}' to '{status}'.",
        actor_id=task.assigned_to,
        details=None
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#tasks", status_code=303)

@router.post("/cases/{case_id}/tasks/{task_id}/delete")
def delete_task(
    case_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    task = db.query(CaseTask).filter(CaseTask.id == task_id, CaseTask.case_id == case_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    title = task.title
    assigned_to = task.assigned_to

    db.delete(task)
    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="task_deleted",
        message=f"Task '{title}' was deleted.",
        actor_id=assigned_to,
        details=None
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#tasks", status_code=303)

@router.post("/cases/{case_id}/tasks/{task_id}/edit")
def edit_task(
    case_id: int,
    task_id: int,
    title: str = Form(...),
    description: str = Form(""),
    status: str = Form(...),
    assigned_to: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    assigned_to = parse_optional_int(assigned_to)

    task = db.query(CaseTask).filter(CaseTask.id == task_id, CaseTask.case_id == case_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    previous_state = {
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "assigned_to": task.assigned_to
    }

    task.title = title
    task.description = description
    task.status = status
    task.assigned_to = assigned_to

    db.commit()

    # Compose a summary of changes
    changes = []
    if previous_state["title"] != title:
        changes.append(f"Title changed from '{previous_state['title']}' to '{title}'")
    if previous_state["description"] != description:
        changes.append("Description updated")
    if previous_state["status"] != status:
        changes.append(f"Status changed from '{previous_state['status']}' to '{status}'")
    if previous_state["assigned_to"] != assigned_to:
        changes.append(f"Reassigned from '{previous_state['assigned_to']}' to '{assigned_to}'")

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="task_edited",
        message=f"Task '{title}' was edited.",
        actor_id=assigned_to,
        details="; ".join(changes) if changes else "No changes detected"
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}#tasks", status_code=303)
