from typing import Optional
from starlette.responses import RedirectResponse
from sqlalchemy import case, func
from fastapi import APIRouter, Request, Depends, Query, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.utils import auth
from app.utils.parser.general_parser_engine import run_parser_for_type
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

    # Load raw JSON from alert
    try:
        source_payload_json = json.loads(alert.source_payload) if alert.source_payload else {}
    except Exception as e:
        source_payload_json = {"error": f"Invalid JSON: {str(e)}"}

    # === Parser Execution ===
    try:
        parsed = run_parser_for_type("alert", source_payload_json, db)
        parsed_fields = parsed.get("mapped_fields", {})
        parsed_tags = parsed.get("tags", [])
        parsed_enrichment = parsed.get("enrichment", {})
        parser_metadata = {
            "parser_name": parsed.get("parser_name"),
            "matched": parsed.get("matched", False)
        }
        print("PARSED:", parsed)
        print("MAPPED:", parsed_fields)
        print("TAGS:", parsed_tags)
        print("ENRICH:", parsed_enrichment)
    except Exception as e:
        parsed_fields = {"error": f"Parser failed: {str(e)}"}
        parsed_tags = []
        parsed_enrichment = {}
        parser_metadata = {"parser_name": "unknown", "matched": False}

    # === MITRE Extraction ===
    mitre_info = source_payload_json.get("rule", {}).get("mitre", {}) or {}
    mitre_ids = mitre_info.get("id", []) if isinstance(mitre_info, dict) else []
    mitre_tactics = mitre_info.get("tactic", []) if isinstance(mitre_info, dict) else []

    # === Related Alerts by Agent ===
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
            func.lower(Alert.source_payload).like(f"%{agent_name.lower()}%")
        )

        total_related = related_query.count()

        related_alerts = related_query.order_by(
            case((Alert.status == "done", 1), else_=0),
            Alert.created_at.desc()
        ).offset(offset).limit(page_size).all()

        for r in related_alerts:
            try:
                payload = json.loads(r.source_payload or "{}")
                parsed = run_parser_for_type("alert", payload, db)
                r.parsed_agent = (
                    parsed.get("mapped_fields", {}).get("agent_name")
                    or parsed.get("mapped_fields", {}).get("agent")
                    or "—"
                )
            except Exception:
                r.parsed_agent = "—"

        total_pages = max((total_related + page_size - 1) // page_size, 1)

    # === Related Alerts by Message ===
    msg_page_size = 10
    msg_offset = (message_page - 1) * msg_page_size

    related_alerts_by_message = []
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
                payload = json.loads(r.source_payload or "{}")
                parsed = run_parser_for_type("alert", payload, db)
                r.parsed_agent = (
                    parsed.get("mapped_fields", {}).get("agent_name")
                    or parsed.get("mapped_fields", {}).get("agent")
                    or "—"
                )
            except Exception:
                r.parsed_agent = "—"

        total_pages_msg = max((total_related_msg + msg_page_size - 1) // msg_page_size, 1)

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

