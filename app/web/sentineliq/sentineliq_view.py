from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from fastapi.templating import Jinja2Templates
from app.models.alert import Alert
from app.utils.parser.general_parser_engine import run_parser_for_type
from app.utils import auth
import json
from typing import Optional
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_eligible_triage_alerts(db: Session):
    alerts = (
        db.query(Alert)
        .filter(Alert.status.in_(["new", "in_progress"]))
        .all()
    )

    eligible = []
    for alert in alerts:
        try:
            payload = json.loads(alert.source_payload or "{}")

            result = run_parser_for_type("triage", payload)


            mapped = result.get("mapped_fields", {})

            if mapped.get("recommended_status") or mapped.get("recommended_resolution") or mapped.get("recommended_action"):
                eligible.append(alert.id)
        except Exception as e:

            continue
    return eligible

@router.get("/sentineliq/triage", response_class=HTMLResponse)
def sentinel_iq_page(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user),
    q: Optional[str] = None,
    min_severity: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    query = db.query(Alert)
    query = query.filter(Alert.status.in_(["new", "in_progress"]))
    toggle = False

    if q:
        query = query.filter(Alert.message.ilike(f"%{q.lower()}%"))

    if min_severity and min_severity.isdigit():
        query = query.filter(Alert.severity >= int(min_severity))

    if status:
        query = query.filter(Alert.status == status)


    # Total count before pagination
    total_alerts = query.count()
    total_pages = max(1, (total_alerts + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))

    # Paginated query
    offset = (page - 1) * page_size
    alerts = query.order_by(Alert.severity.desc()).offset(offset).limit(page_size).all()

    # Triage processing
    triaged_alerts = []
    triage_eligible_count = 0
    for alert in alerts:
        try:
            payload = json.loads(alert.source_payload) if alert.source_payload else {}
            triage_result = run_parser_for_type("triage", payload)
            alert.triage_result = triage_result
            mapped = triage_result.get("mapped_fields", {})

            if mapped.get("recommended_status") or mapped.get("recommended_resolution"):
                triage_eligible_count += 1
        except Exception as e:
            alert.triage_result = {"error": str(e)}

        triaged_alerts.append(alert)

    return templates.TemplateResponse("sentinel_iq/sentinel_iq.html", {
        "request": request,
        "alerts": triaged_alerts,
        "triage_eligible_count": triage_eligible_count,
        "pagination": {
            "total_alerts": total_alerts,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size,
        }
    })



@router.post("/sentineliq/triage/all")
def triage_all_alerts(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    alerts = (
        db.query(Alert)
        .filter(Alert.status.in_(["new", "in_progress"]))
        .all()
    )

    for alert in alerts:
        try:
            payload = json.loads(alert.source_payload or "{}")
            result = run_parser_for_type("triage", payload)
            mapped = result.get("mapped_fields", {})

            if mapped.get("recommended_status") or mapped.get("recommended_resolution") or mapped.get("recommended_action"):
                if mapped.get("recommended_status"):
                    alert.status = mapped["recommended_status"]
                if mapped.get("recommended_resolution"):
                    alert.resolution = mapped["recommended_resolution"]
                if mapped.get("recommended_action"):
                    alert.resolution_comment = f"Auto-applied: {mapped['recommended_action']}"
        except:
            continue

    db.commit()
    return RedirectResponse(url="/web/v1/sentineliq/triage", status_code=303)

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