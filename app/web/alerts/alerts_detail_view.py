from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import SessionLocal
from app.models.alert import Alert
from app.utils.parser.general_parser_engine import run_parser_for_type  # ✅ New engine!
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

@router.get("/alerts/{alert_id}", response_class=HTMLResponse)
def alert_detail_view(alert_id: int, request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

    try:
        source_payload_json = json.loads(alert.source_payload) if alert.source_payload else {}
    except Exception as e:
        source_payload_json = {"error": f"Invalid JSON: {str(e)}"}

    try:
        parsed = run_parser_for_type("alert", source_payload_json)  # ✅ Use new parser engine
        parsed_fields = parsed.get("mapped_fields", {})
        parsed_tags = parsed.get("tags", [])
        parsed_enrichment = parsed.get("enrichment", {})
    except Exception as e:
        parsed_fields = {"error": f"Parser failed: {str(e)}"}
        parsed_tags = []
        parsed_enrichment = {}

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

    return templates.TemplateResponse("alerts/alert_detail.html", {
        "request": request,
        "alert": alert,
        "rendered_sections": rendered_sections,
        "source_payload_json": source_payload_json,
        "parsed_tags": parsed_tags,
        "parsed_enrichment": parsed_enrichment
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

@router.get("/alerts/{alert_id}/quick/apply")
def quick_apply_recommendation(alert_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    import json
    from app.utils.parser.general_parser_engine import run_parser_for_type

    print("inside statement")
    payload = json.loads(alert.source_payload) if alert.source_payload else {}
    triage_result = run_parser_for_type("triage", payload)
    fields = triage_result.get("mapped_fields", {})

    status = fields.get("recommended_status")
    resolution = fields.get("recommended_resolution")
    comment = fields.get("recommended_action")

    if status:
        alert.status = status
    if resolution:
        alert.resolution = resolution
    if comment:
        alert.resolution_comment = f"Auto-applied: {comment}"

    db.commit()
    return RedirectResponse(f"/web/v1/sentineliq/triage", status_code=303)