from typing import Optional
from starlette.responses import RedirectResponse
from sqlalchemy import case, func, text
from fastapi import APIRouter, Request, Depends, Query, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import CaseTimelineEvent
from app.models.alert import Alert
from app.models.case import Case
from app.utils import auth
from app.utils.parser.general_parser_engine import run_parser_for_type
import json
from sqlalchemy import Text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def safe_get_agent_name(payload: dict) -> str:
    if not isinstance(payload, dict):
        return "—"
    agent = payload.get("agent")
    if isinstance(agent, dict):
        return agent.get("name") or "—"
    elif isinstance(agent, str):
        return agent
    host = payload.get("host")
    if isinstance(host, dict):
        return host.get("name") or "—"
    elif isinstance(host, str):
        return host
    return "—"

@router.get("/alerts/{alert_id}", response_class=HTMLResponse)
def alert_detail_view(
    alert_id: int,
    request: Request,
    page: int = Query(1, ge=1),
    message_page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    try:
        if isinstance(alert.source_payload, str):
            source_payload_json = json.loads(alert.source_payload)
        elif isinstance(alert.source_payload, dict):
            source_payload_json = alert.source_payload
        else:
            source_payload_json = {}
    except Exception as e:
        source_payload_json = {"error": f"Invalid JSON: {str(e)}"}

    try:
        parsed = run_parser_for_type("alert", source_payload_json, db)
        parsed_fields = parsed.get("mapped_fields", {})
        parsed_tags = parsed.get("tags", [])
        parsed_enrichment = parsed.get("enrichment", {})
        parser_metadata = {
            "parser_name": parsed.get("parser_name"),
            "matched": parsed.get("matched", False)
        }
    except Exception as e:
        parsed_fields = {"error": f"Parser failed: {str(e)}"}
        parsed_tags = []
        parsed_enrichment = {}
        parser_metadata = {"parser_name": "unknown", "matched": False}

    mitre_info = source_payload_json.get("rule", {}).get("mitre", {}) or {}
    mitre_ids = mitre_info.get("id", []) if isinstance(mitre_info, dict) else []
    mitre_tactics = mitre_info.get("tactic", []) if isinstance(mitre_info, dict) else []

    page_size = 10
    offset = (page - 1) * page_size

    raw_agent = parsed_fields.get("agent_name") or parsed_fields.get("agent")
    agent_name = raw_agent if isinstance(raw_agent, str) else None

    related_alerts = []
    total_related = 0
    total_pages = 1

    if agent_name:
        related_query = db.query(Alert).filter(
            Alert.id != alert.id,
            func.lower(func.cast(Alert.source_payload, Text)).like(f"%{agent_name.lower()}%")
        )

        total_related = related_query.count()

        related_alerts = related_query.order_by(
            case((Alert.status == "done", 1), else_=0),
            Alert.created_at.desc()
        ).offset(offset).limit(page_size).all()

        for r in related_alerts:
            try:
                if isinstance(r.source_payload, dict):
                    payload = r.source_payload
                elif isinstance(r.source_payload, str):
                    payload = json.loads(r.source_payload or "{}")
                else:
                    payload = {}

                parsed_r = run_parser_for_type("alert", payload, db)
                r.parsed_agent = (
                    parsed_r.get("mapped_fields", {}).get("agent_name")
                    or parsed_r.get("mapped_fields", {}).get("agent")
                    or "—"
                )
            except Exception as e:
                print(f"Failed to parse related alert {r.id}: {e}")
                r.parsed_agent = "—"

        total_pages = max((total_related + page_size - 1) // page_size, 1)

    msg_page_size = 10
    msg_offset = (message_page - 1) * msg_page_size

    related_alerts_by_message = []   # ✅ always initialized
    total_related_msg = 0
    total_pages_msg = 1

    if alert.message:
        related_msg_query = db.query(Alert).filter(
            Alert.id != alert.id,
            Alert.message == alert.message,
            Alert.status != "done"
        )

        total_related_msg = related_msg_query.count()

        related_alerts_by_message = related_msg_query.order_by(
            Alert.created_at.desc()
        ).offset(msg_offset).limit(msg_page_size).all()

        for r in related_alerts_by_message:
            try:
                if isinstance(r.source_payload, dict):
                    payload = r.source_payload
                elif isinstance(r.source_payload, str):
                    payload = json.loads(r.source_payload or "{}")
                else:
                    payload = {}

                parsed_r = run_parser_for_type("alert", payload, db)
                r.parsed_agent = (
                    parsed_r.get("mapped_fields", {}).get("agent_name")
                    or parsed_r.get("mapped_fields", {}).get("agent")
                    or "—"
                )
            except Exception as e:
                print(f"Failed to parse related alert {r.id}: {e}")
                r.parsed_agent = "—"

        total_pages_msg = max((total_related_msg + msg_page_size - 1) // msg_page_size, 1)

    cases = db.query(Case).order_by(Case.created_at.desc()).limit(20).all()

    return templates.TemplateResponse("alerts/alert_detail.html", {
        "request": request,
        "alert": alert,
        "parsed_fields": parsed_fields,
        "parsed_tags": parsed_tags,
        "parsed_enrichment": parsed_enrichment,
        "parser_metadata": parser_metadata,
        "source_payload_json": source_payload_json,
        "related_alerts": related_alerts,
        "related_total": total_related,
        "related_page": page,
        "related_pages": total_pages,
        "related_alerts_by_message": related_alerts_by_message,
        "related_total_msg": total_related_msg,
        "related_page_msg": message_page,
        "related_pages_msg": total_pages_msg,
        "mitre_ids": mitre_ids,
        "mitre_tactics": mitre_tactics,
        "mitre_info": mitre_info,
        "cases": cases,
    })



@router.post("/alerts/{alert_id}/update")
def update_alert_form(
    alert_id: int,
    status: Optional[str] = Form(None),
    resolution: Optional[str] = Form(None),
    resolution_comment: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if status:
        alert.status = status
    if resolution:
        alert.resolution = resolution
    if resolution_comment is not None:
        alert.resolution_comment = resolution_comment

    db.commit()
    return RedirectResponse(f"/web/v1/alerts/{alert_id}", status_code=303)


@router.get("/alerts/{alert_id}/quick/{action}")
def quick_triage_action(alert_id: int, action: str, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if action == "legit":
        alert.status = "done"
        alert.resolution = "legitimate"
        alert.resolution_comment = "Marked legitimate by Sentinel IQ"
    elif action == "fp":
        alert.status = "done"
        alert.resolution = "false_positive"
        alert.resolution_comment = "Marked false positive by Sentinel IQ"
    elif action == "escalate":
        alert.status = "in_progress"
        alert.resolution_comment = "Escalated by Sentinel IQ"

    db.commit()
    return RedirectResponse(f"/web/v1/sentineliq/triage", status_code=303)


@router.post("/alerts/{alert_id}/promote")
def promote_alert_to_case(
    alert_id: int,
    action: str = Form(...),
    existing_case_id: Optional[int] = Form(None),
    case_title: Optional[str] = Form(None),
    case_description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if action == "new_case":
        if not case_title:
            raise HTTPException(status_code=400, detail="Case title is required.")

        new_case = Case(
            title=case_title,
            description=case_description or "",
            state="new"
        )
        db.add(new_case)
        db.flush()
        alert.case_id = new_case.id

        timeline_event = CaseTimelineEvent(
            case_id=new_case.id,
            actor_id=user.id,
            event_type="alert_promoted",
            message=f"Alert {alert.id} promoted to new case.",
            details=alert.message[:255] if alert.message else None,
        )
        db.add(timeline_event)
        db.commit()
        return RedirectResponse(f"/web/v1/cases/{new_case.id}", status_code=303)

    elif action == "existing_case":
        if not existing_case_id:
            raise HTTPException(status_code=400, detail="No existing case selected.")
        alert.case_id = existing_case_id

        timeline_event = CaseTimelineEvent(
            case_id=existing_case_id,
            actor_id=user.id,
            event_type="alert_linked",
            message=f"Alert {alert.id} attached to existing case.",
            details=alert.message[:255] if alert.message else None,
        )
        db.add(timeline_event)
        db.commit()
        return RedirectResponse(f"/web/v1/cases/{existing_case_id}", status_code=303)

    elif action == "bulk_promote":
        if not alert.message:
            raise HTTPException(status_code=400, detail="Alert message is required for bulk promote.")

        existing_case = db.query(Case).filter(
            Case.state != "closed",
            func.lower(Case.title).like(f"%{alert.message.lower()}%") |
            func.lower(Case.description).like(f"%{alert.message.lower()}%")
        ).first()

        if existing_case:
            target_case = existing_case
        else:
            new_case = Case(
                title=f"Case for Message: {alert.message[:60]}",
                description=f"Auto-created by Smart Bulk Promote: {alert.message}",
                state="new"
            )
            db.add(new_case)
            db.flush()
            target_case = new_case

        same_msg_alerts = db.query(Alert).filter(
            Alert.message == alert.message
        ).all()

        for a in same_msg_alerts:
            a.case_id = target_case.id
            timeline_event = CaseTimelineEvent(
                case_id=target_case.id,
                actor_id=user.id,
                event_type="alert_linked",
                message=f"Alert {a.id} linked by Smart Bulk Promote.",
                details=a.message[:255] if a.message else None,
            )
            db.add(timeline_event)

        db.commit()
        return RedirectResponse(f"/web/v1/cases/{target_case.id}", status_code=303)

    raise HTTPException(status_code=400, detail="Invalid action.")


@router.get("/alerts/{alert_id}/bulk_promote")
def smart_bulk_promote(
    alert_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert or not alert.message:
        raise HTTPException(status_code=404, detail="Alert not found or no message to correlate.")

    existing_case = db.query(Case).filter(
        Case.state != "closed",
        func.lower(Case.title).like(f"%{alert.message.lower()}%") |
        func.lower(Case.description).like(f"%{alert.message.lower()}%")
    ).first()

    if existing_case:
        target_case = existing_case
    else:
        new_case = Case(
            title=f"Case for Alert Message: {alert.message[:60]}",
            description=f"Auto-created from alert #{alert.id} with message:\n\n{alert.message}",
            state="new"
        )
        db.add(new_case)
        db.flush()
        target_case = new_case

    same_msg_alerts = db.query(Alert).filter(
        Alert.message == alert.message,
        Alert.case_id == None
    ).all()

    for a in same_msg_alerts:
        a.case_id = target_case.id
        timeline_event = CaseTimelineEvent(
            case_id=target_case.id,
            actor_id=user.id,
            event_type="alert_linked",
            message=f"Alert {a.id} linked to case by Smart Bulk Promote.",
            details=a.message[:255] if a.message else None,
        )
        db.add(timeline_event)

    db.commit()

    return RedirectResponse(f"/web/v1/cases/{target_case.id}", status_code=303)
