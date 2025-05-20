from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from fastapi.templating import Jinja2Templates
from app.models.alert import Alert
from app.utils.parser.general_parser_engine import run_parser_for_type
from app.utils import auth
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/sentineliq/triage", response_class=HTMLResponse)
def sentinel_iq_page(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    recent_alerts = (
        db.query(Alert)
        .filter(Alert.status.in_(["new", "in_progress"]))
        .order_by(Alert.severity.desc())
        .limit(50)
        .all()
    )

    triaged_alerts = []
    for alert in recent_alerts:
        try:
            payload = json.loads(alert.source_payload) if alert.source_payload else {}
            #print(payload)
            triage_result = run_parser_for_type("triage", payload)
            #print(f"[Triage] Alert #{alert.id} → {triage_result}")
            alert.triage_result = triage_result
        except Exception as e:
            alert.triage_result = {"error": str(e)}

        triaged_alerts.append(alert)

    return templates.TemplateResponse("sentinel_iq/sentinel_iq.html", {
        "request": request,
        "page_title": "Sentinel IQ",
        "intro": "This module will handle automatic alert triage using rules, enrichment, and smart logic.",
        "alerts": triaged_alerts
    })

@router.get("/alerts/{alert_id}/quick/res/{res_key}")
def quick_resolution_action(alert_id: int, res_key: str, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Resolution → status map
    resolution_status_map = {
        "unknown": "in_progress",
        "under_investigation": "in_progress",
        "false_positive": "done",
        "true_positive_no_impact": "done",
        "true_positive_with_impact": "in_progress",
        "not_applicable": "done",
        "legitimate": "done",
    }

    alert.resolution = res_key
    alert.status = resolution_status_map.get(res_key, alert.status)
    alert.resolution_comment = f"Marked as {res_key.replace('_', ' ').title()} via quick action"
    db.commit()

    return RedirectResponse(f"/web/v1/sentineliq/triage", status_code=303)

@router.get("/sentineliq/triage/{alert_id}/quick/apply")
def quick_apply_recommendation(alert_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

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