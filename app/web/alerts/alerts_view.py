from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Query, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.case import Case
from urllib.parse import urlencode
from app.utils.parser.compat_parser_runner import run_parser_for_type
import json
from app.utils import auth
from collections import Counter
from app.models.case_timeline import CaseTimelineEvent

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Hacky to get it to work
# @TODO: Fix this
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

SEVERITY_MAP = {
    "informational": [0],
    "low": [1, 2, 3, 4, 5, 6],
    "medium": [7, 8, 9, 10, 11],
    "high": [12, 13, 14,],
    "critical": [15],
}

SEVERITY_LABELS = {
    0: "Informational",
    1: "Low", 2: "Low", 3: "Low", 4: "Low", 5: "Low", 6: "Low",
    7: "Medium", 8: "Medium", 9: "Medium", 10: "Medium", 11: "Medium",
    12: "High", 13: "High", 14: "High",
    15: "Critical"
}

SEVERITY_CSS_CLASSES = {
    "Informational": "severity-info",
    "Low": "severity-low",
    "Medium": "severity-medium",
    "High": "severity-high",
    "Critical": "severity-critical"
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/alerts", response_class=HTMLResponse)
def list_alerts_view(
    request: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=1000),
    source: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    start_event_time: Optional[str] = Query(None),
    end_event_time: Optional[str] = Query(None),
    raw_alert_id: Optional[str] = Query(None, alias="alert_id"),
    severity: Optional[str] = Query(None),
    resolution: Optional[str] = Query(None),
    user=Depends(auth.get_current_user)
):
    offset = (page - 1) * limit
    query = db.query(Alert)

    if raw_alert_id:
        try:
            alert_id = int(raw_alert_id)
            query = query.filter(Alert.id == alert_id)
        except ValueError:
            pass

    if source:
        query = query.filter(Alert.source == source)

    if resolution:
        resolution_values = [r.strip() for r in resolution.split(",") if r.strip()]
        query = query.filter(Alert.resolution.in_(resolution_values))

    if status:
        status_values = [s.strip() for s in status.split(",") if s.strip()]
        query = query.filter(Alert.status.in_(status_values))
    else:
        query = query.filter(Alert.status.in_(["new", "in_progress"]))

    if tags:
        tag_values = [tag.strip() for tag in tags.split(",") if tag.strip()]
        for tag in tag_values:
            query = query.filter(Alert.tags.ilike(f"%{tag}%"))

    if search:
        query = query.filter(Alert.message.ilike(f"%{search}%"))

    if start_time:
        query = query.filter(Alert.created_at >= start_time)
    if end_time:
        query = query.filter(Alert.created_at <= end_time)
    if start_event_time:
        query = query.filter(Alert.source_event_time >= start_event_time)
    if end_event_time:
        query = query.filter(Alert.source_event_time <= end_event_time)

    severity__in = None
    try:
        severity_int = int(severity) if severity else None
    except ValueError:
        severity__in = SEVERITY_MAP.get(severity.lower(), None)

    if severity__in:
        query = query.filter(Alert.severity.in_(severity__in))
    elif severity:
        try:
            severity_int = int(severity)
            query = query.filter(Alert.severity == severity_int)
        except ValueError:
            pass

    total = query.count()
    alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    for alert in alerts:
        try:
            payload = json.loads(alert.source_payload or "{}")
            parsed = run_parser_for_type("alert", payload)

            mapped = parsed.get("mapped_fields", {}) or {}

            # Ensure agent_name always exists
            if "agent_name" not in mapped:
                agent_name = payload.get("agent", {}).get("name")
                if agent_name:
                    mapped["agent_name"] = agent_name
                    mapped["agent"] = agent_name  # fallback display

            alert.parsed_fields = mapped

        except Exception as e:
            # Fallback parse
            try:
                payload = json.loads(alert.source_payload or "{}")
                agent_name = payload.get("agent", {}).get("name")
                alert.parsed_fields = {
                    "agent_name": agent_name,
                    "agent": agent_name
                }
            except Exception:
                alert.parsed_fields = {}

    for alert in alerts:
        alert.created_at_formatted = alert.created_at.strftime("%Y-%m-%d %H:%M:%S") if alert.created_at else "-"
        alert.severity_label = SEVERITY_LABELS.get(alert.severity, "Unknown")
        alert.severity_class = SEVERITY_CSS_CLASSES.get(alert.severity_label, "severity-unknown")

    total_pages = (total // limit) + (1 if total % limit else 0)

    query_dict = {
        "source": source,
        "status": status,
        "resolution": resolution,
        "severity": severity,
        "limit": limit,
        "alert_id": raw_alert_id,
        "tags": tags,
        "search": search,
        "start_time": start_time,
        "end_time": end_time,
        "start_event_time": start_event_time,
        "end_event_time": end_event_time,
    }
    query_base = urlencode({k: v for k, v in query_dict.items() if v})

    pagination = {
        "page": page,
        "limit": limit,
        "total_results": total,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None,
        "show_prev": page > 1,
        "show_next": page < total_pages,
        "total_pages": total_pages,
        "query_string": query_base,
    }
    cases = db.query(Case).order_by(Case.created_at.desc()).limit(20).all()

    return templates.TemplateResponse("alerts/alerts.html", {
        "request": request,
        "alerts": alerts,
        "page": page,
        "limit": limit,
        "source": source or "",
        "status": status or "",
        "severity": severity or "",
        "pagination": pagination,
        "cases": cases
    })


@router.post("/alerts/bulk_update")
async def bulk_update_alerts(
    alert_ids: str = Form(...),
    status: Optional[str] = Form(None),
    resolution: Optional[str] = Form(None),
    comment: Optional[str] = Form(None),
    return_to: Optional[str] = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    ids = [int(id_.strip()) for id_ in alert_ids.split(",") if id_.strip()]
    if not ids:
        raise HTTPException(status_code=400, detail="No alert IDs provided.")

    alerts = db.query(Alert).filter(Alert.id.in_(ids)).all()

    if status:
        for alert in alerts:
            alert.status = status
    if resolution:
        for alert in alerts:
            alert.resolution = resolution
    if comment:
        for alert in alerts:
            alert.resolution_comment = comment

    db.commit()

    # Preserve filters after bulk update
    redirect_url = f"/web/v1/alerts?{return_to}" if return_to else "/web/v1/alerts"
    return RedirectResponse(redirect_url, status_code=303)



@router.get("/alerts/tags", response_class=HTMLResponse)
def view_all_tags(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    tag_query = db.query(Alert.tags).filter(Alert.tags.isnot(None)).all()
    tag_list = []

    for row in tag_query:
        if row.tags:
            tag_list.extend(tag.strip() for tag in row.tags.split(",") if tag.strip())

    tag_counter = Counter(tag_list)
    tags_data = [{"tag": tag, "count": count} for tag, count in tag_counter.items()]
    tags_data.sort(key=lambda x: x["count"], reverse=True)

    return templates.TemplateResponse("alerts/tags.html", {
        "request": request,
        "tags": tags_data
    })

@router.post("/alerts/merge", response_class=HTMLResponse)
def merge_alerts(
    request: Request,
    user=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
    alert_ids: str = Form(...),
    action: str = Form(...),
    existing_case_id: Optional[int] = Form(None),
    case_title: Optional[str] = Form(None),
    case_description: Optional[str] = Form(None)
):
    alert_id_list = [int(aid) for aid in alert_ids.split(",") if aid.strip().isdigit()]
    alerts = db.query(Alert).filter(Alert.id.in_(alert_id_list)).all()

    if not alerts:
        raise HTTPException(status_code=400, detail="No valid alerts selected.")

    if action == "new_case":
        if not case_title:
            raise HTTPException(status_code=400, detail="Case title is required.")

        new_case = Case(
            title=case_title,
            description=case_description or "",
            state="new",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_case)
        db.flush()

        for alert in alerts:
            alert.case_id = new_case.id
            log_timeline_event(
                db=db,
                case_id=new_case.id,
                event_type="alert_linked",
                message=f"Alert {alert.id} linked to new case from merge.",
                details=alert.message[:255] if alert.message else None
            )

        db.commit()
        return RedirectResponse(f"/web/v1/cases/{new_case.id}", status_code=303)

    elif action == "existing_case":
        if not existing_case_id:
            raise HTTPException(status_code=400, detail="No existing case selected.")

        for alert in alerts:
            alert.case_id = existing_case_id
            db.flush()
            log_timeline_event(
                db=db,
                case_id=existing_case_id,
                event_type="alert_linked",
                message=f"Alert {alert.id} linked to existing case from merge.",
                details=alert.message[:255] if alert.message else None
            )

        db.commit()
        return RedirectResponse(f"/web/v1/cases/{existing_case_id}", status_code=303)

    raise HTTPException(status_code=400, detail="Invalid action.")

