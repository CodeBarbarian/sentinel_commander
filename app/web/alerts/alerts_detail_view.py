from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import case

from starlette.responses import RedirectResponse

from app.core.database import SessionLocal
from app.models.alert import Alert
from app.utils.parser.general_parser_engine import run_parser_for_type
from app.utils.parser.renderer import render_alert_detail_fields
import json
from app.utils import auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import case
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.utils import auth
from app.utils.parser.general_parser_engine import run_parser_for_type
from app.utils.parser.renderer import render_alert_detail_fields
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

    # Parser Execution
    try:
        parsed = run_parser_for_type("alert", source_payload_json)
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

    # Optional: if needed for legacy rendering or fallback accordion layout
    rendered_sections = render_alert_detail_fields(
        alert.__dict__,
        parsed_fields,
        extra_context={
            "parsed_fields": parsed_fields,
            "parsed_tags": parsed_tags,
            "parsed_enrichment": parsed_enrichment,
            "source_payload_json": source_payload_json
        }
    )

    # === Related Alerts (Paginated, based on agent.name) ===
    page_size = 10
    offset = (page - 1) * page_size

    # Ensure we have an agent to match on
    agent_name = parsed_fields.get("agent") if isinstance(parsed_fields.get("agent"), str) else None

    related_alerts = []
    total_related = 0
    total_pages = 1

    if agent_name:
        related_query = db.query(Alert).filter(
            Alert.id != alert.id,
            Alert.source_payload.contains(agent_name)
        )
        # Inject parsed_fields.agent into each related alert manually
        for r in related_alerts:
            try:
                payload = json.loads(r.source_payload or "{}")
                parsed = run_parser_for_type("alert", payload)
                r.parsed_agent = parsed.get("mapped_fields", {}).get("agent", "—")
            except Exception:
                r.parsed_agent = "—"

        total_related = related_query.count()

        related_alerts = related_query.order_by(
            case((Alert.status == "done", 1), else_=0),
            Alert.created_at.desc()
        ).offset(offset).limit(page_size).all()

        total_pages = max((total_related + page_size - 1) // page_size, 1)

    return templates.TemplateResponse("alerts/alert_detail.html", {
        "request": request,
        "alert": alert,
        "parsed_fields": parsed_fields,
        "parsed_tags": parsed_tags,
        "parsed_enrichment": parsed_enrichment,
        "parser_metadata": parser_metadata,
        "source_payload_json": source_payload_json,
        "rendered_sections": rendered_sections,
        "related_alerts": related_alerts,
        "related_total": total_related,
        "related_page": page,
        "related_pages": total_pages,
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

