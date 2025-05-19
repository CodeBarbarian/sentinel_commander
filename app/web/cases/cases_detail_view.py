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
from datetime import datetime


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

@router.get("/cases/{case_id}", response_class=HTMLResponse)
def view_case(request: Request, case_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    case = (
        db.query(Case)
        .options(
            joinedload(Case.customer),
            joinedload(Case.assigned_user),
            joinedload(Case.tags),
            joinedload(Case.notes).joinedload(CaseNote.author),
        )
        .filter(Case.id == case_id)
        .first()
    )

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    customers = db.query(Customer).all()
    print(customers)
    users = db.query(User).all()

    notes = db.query(CaseNote).filter(CaseNote.case_id == case_id).all()
    note_objects = [CaseNoteOut.from_orm_with_author(note) for note in notes]

    tasks = db.query(CaseTask).filter(CaseTask.case_id == case_id).all()
    task_objects = [CaseTaskOut.from_orm_with_assignee(task) for task in tasks]

    iocs = db.query(CaseIOC).filter(CaseIOC.case_id == case_id).all()
    ioc_objects = [CaseIOCOut.model_validate(ioc) for ioc in iocs]

    evidence = db.query(CaseEvidence).filter(CaseEvidence.case_id == case_id).all()
    evidence_objects = [CaseEvidenceOut.model_validate(e) for e in evidence]

    alerts = db.query(Alert).filter(Alert.case_id == case_id).all()

    linked_assets = case.assets
    linked_asset_objects = [AssetOut.model_validate(a) for a in linked_assets]

    all_assets = db.query(Asset).all()

    timeline_entries = (
        db.query(CaseTimelineEvent)
        .filter(CaseTimelineEvent.case_id == case_id)
        .order_by(CaseTimelineEvent.timestamp.desc())
        .all()
    )

    timeline_objects = [CaseTimelineOut.model_validate(entry) for entry in timeline_entries]
    linked_playbooks = (
        db.query(Playbook)
        .join(CasePlaybook, CasePlaybook.playbook_id == Playbook.id)
        .filter(CasePlaybook.case_id == case_id)
        .all()
    )

    linked_playbook_objects = []
    for p in linked_playbooks:
        rendered_steps = markdown.markdown(p.steps or "", extensions=["fenced_code", "tables"])
        pb_out = PlaybookOut.model_validate(p)
        pb_out.rendered_steps = rendered_steps  # add custom attribute
        linked_playbook_objects.append(pb_out)

    all_playbooks = db.query(Playbook).all()


    return templates.TemplateResponse(
        "cases/cases_detail.html",
        {
            "request": request,
            "case": case,
            "customer_name": case.customer.name if case.customer else "—",
            "assigned_to_username": case.assigned_user.username if case.assigned_user else "Unassigned",
            "customers": customers,
            "users": users,
            "notes": note_objects,
            "tasks": task_objects,
            "iocs": ioc_objects,
            "evidence": evidence_objects,
            "timeline": timeline_objects,
            "alerts": alerts,
            "assets": linked_asset_objects,
            "all_assets": all_assets,
            "playbooks": linked_playbook_objects,
            "all_playbooks": all_playbooks,
        },
    )

@router.post("/cases/{case_id}/update")
def update_case(
    case_id: int,
    request: Request,
    customer_id: int = Form(...),
    assigned_to_raw: str = Form(""),
    classification: str = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    state: str = Form(...),
    severity: str = Form(...),
    tags: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    assigned_to = parse_optional_int(assigned_to_raw)

    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.customer_id = customer_id
    case.assigned_to = assigned_to
    case.classification = classification
    case.title = title
    case.description = description
    case.state = state
    case.severity = severity
    case.tags.clear()

    db.flush()
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    case.tags = [CaseTag(tag=tag) for tag in tag_list]

    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="case_updated",
        message=f"Case updated: title='{title}', assigned_to={assigned_to}",
        actor_id=None,  # You could parse this from the request/session if available
        details=f"Classification: {classification}, State: {state}"
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}", status_code=303)

@router.post("/cases/{case_id}/close")
def close_case(
    case_id: int,
    note: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    if not note.strip():
        raise HTTPException(status_code=400, detail="Closing note is required.")

    case.state = "done"
    case.closing_note = note.strip()
    case.closed_at = datetime.utcnow()

    db.commit()

    log_timeline_event(
        db=db,
        case_id=case_id,
        event_type="case_closed",
        message="Case was closed.",
        details=note[:255]
    )

    return RedirectResponse(url=f"/web/v1/cases/{case_id}", status_code=303)
