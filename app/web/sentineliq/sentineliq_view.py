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
    only_eligible: bool = False,
    page: int = 1,
    page_size: int = 50,
):
    query = db.query(Alert).filter(Alert.status.in_(["new", "in_progress",]))

    if q:
        query = query.filter(Alert.message.ilike(f"%{q.lower()}%"))

    if min_severity and min_severity.isdigit():
        query = query.filter(Alert.severity >= int(min_severity))

    if status:
        query = query.filter(Alert.status == status)

    all_alerts = query.order_by(Alert.severity.desc()).all()
    triaged_alerts = []
    triage_eligible_count = 0

    for alert in all_alerts:
        try:
            payload = alert.source_payload or {}
            if isinstance(payload, str):
                payload = json.loads(payload)

            triage_result = run_parser_for_type("triage", payload)
            mapped = triage_result.get("mapped_fields", {})

            triage_result.setdefault("mapped_fields", {})
            triage_result.setdefault("recommended_status", None)
            triage_result.setdefault("recommended_resolution", None)
            triage_result.setdefault("recommended_action", None)

            eligible = mapped.get("recommended_status") or mapped.get("recommended_resolution") or mapped.get("recommended_action")
            if eligible:
                triage_eligible_count += 1

            alert.triage_result = triage_result

            if only_eligible and not eligible:
                continue

            triaged_alerts.append(alert)

        except Exception as e:
            alert.triage_result = {
                "error": str(e),
                "mapped_fields": {},
                "recommended_status": None,
                "recommended_resolution": None,
                "recommended_action": None
            }
            if not only_eligible:
                triaged_alerts.append(alert)

    # Pagination after filtering
    total_alerts = len(triaged_alerts)
    total_pages = max(1, (total_alerts + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    paginated_alerts = triaged_alerts[start:end]

    return templates.TemplateResponse("sentinel_iq/sentinel_iq.html", {
        "request": request,
        "alerts": paginated_alerts,
        "triage_eligible_count": triage_eligible_count,
        "only_eligible": only_eligible,
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
            payload = alert.source_payload or {}

            if isinstance(payload, str):
                payload = json.loads(payload)

            result = run_parser_for_type("triage", payload)
            mapped = result.get("mapped_fields", {})

            if mapped.get("recommended_status") or mapped.get("recommended_resolution") or mapped.get("recommended_action"):
                if mapped.get("recommended_status"):
                    alert.status = mapped["recommended_status"]
                if mapped.get("recommended_resolution"):
                    alert.resolution = mapped["recommended_resolution"]
                if mapped.get("recommended_action"):
                    alert.resolution_comment = f"Auto-applied: {mapped['recommended_action']}"
        except Exception as e:
            print(f"[Triage All] Failed to process alert {alert.id}: {e}")
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
def quick_apply_recommendation(
    alert_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    payload = alert.source_payload or {}

    if isinstance(payload, str):
        payload = json.loads(payload)

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
