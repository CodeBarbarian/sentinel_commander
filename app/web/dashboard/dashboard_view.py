from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.source import Source
from app.models.case import Case
from app.utils import auth
import json
from app.utils.parser.compat_parser_runner import run_parser_for_type
from app.utils.severity import SEVERITY_LABELS, SEVERITY_CSS_CLASSES, SEVERITY_MAP

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_view(request: Request, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    now = datetime.utcnow()
    start_of_day = datetime(now.year, now.month, now.day)

    # Stats
    alerts_today = db.query(func.count(Alert.id)).filter(Alert.created_at >= start_of_day).scalar()
    open_cases = db.query(func.count(Case.id)).filter(Case.state != "closed").scalar()
    source_count = db.query(func.count(Source.id)).scalar()

    # Count unique tags – assumes tags is a comma-separated string, adjust if tags are stored differently
    tag_query = db.query(Alert.tags).filter(Alert.tags.isnot(None)).all()
    tag_set = set()
    for row in tag_query:
        if row.tags:
            tag_set.update(tag.strip() for tag in row.tags.split(",") if tag.strip())
    unique_tags = len(tag_set)

    # Severity breakdown for today only
    severity_levels = ["Informational", "Low", "Medium", "High", "Critical"]
    severity_counts = []
    for label in severity_levels:
        values = SEVERITY_MAP[label]
        count = db.query(func.count(Alert.id)).filter(
            Alert.severity.in_(values),
            Alert.created_at >= start_of_day
        ).scalar()
        severity_counts.append(count)

    # Alerts per day for last 7 days
    timeline_labels = []
    timeline_values = []
    for i in range(6, -1, -1):
        day = now.date() - timedelta(days=i)
        count = db.query(func.count(Alert.id)).filter(func.date(Alert.created_at) == day).scalar()
        timeline_labels.append(day.strftime("%A (%d %b)"))
#        timeline_labels.append(day.strftime("%a"))
        timeline_values.append(count)

    # Get latest 5 alerts
    alerts_raw = (
        db.query(Alert, Source.display_name)
        .join(Source, Source.id == Alert.source_id, isouter=True)
        .order_by(Alert.created_at.desc())
        .limit(5)
        .all()
    )

    recent_alerts = []
    for alert, display_name in alerts_raw:
        alert_dict = alert.__dict__.copy()
        alert_dict["source_display_name"] = display_name

        # Parse source_payload
        try:
            payload = json.loads(alert.source_payload or "{}")
            parsed = run_parser_for_type("alert", payload)
            parsed_fields = parsed.get("mapped_fields", {})
            alert_dict["parsed_fields"] = parsed_fields
            alert_dict["parsed_tags"] = parsed.get("tags", [])
        except Exception:
            alert_dict["parsed_fields"] = {}
            alert_dict["parsed_tags"] = []

        # Tactical defaults
        alert_dict["agent_name"] = alert_dict["parsed_fields"].get("agent_name", "—")
        alert_dict["severity_label"] = SEVERITY_LABELS.get(alert.severity, "Unknown")
        alert_dict["severity_class"] = SEVERITY_CSS_CLASSES.get(alert_dict["severity_label"], "severity-unknown")

        recent_alerts.append(alert_dict)

    status_counts = db.query(Alert.status, func.count(Alert.id)).group_by(Alert.status).all()
    status_labels = [row[0] for row in status_counts]
    status_values = [row[1] for row in status_counts]

    return templates.TemplateResponse("dashboard/dashboard.html", {
        "request": request,
        "stats": {
            "alerts_today": alerts_today,
            "open_cases": open_cases,
            "sources": source_count,
            "unique_tags": unique_tags
        },
        "charts": {
            "severity_labels": severity_levels,
            "severity_values": severity_counts,
            "timeline_labels": timeline_labels,
            "timeline_values": timeline_values
        },
        "recent_alerts": recent_alerts,
        "status_labels": status_labels,
        "status_values": status_values,
    })

@router.get("/dashboard/operator", response_class=HTMLResponse)
def operator_dashboard_view(request: Request, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    # Critical Alerts (severity == 15)
    critical_alerts = db.query(func.count(Alert.id)).filter(Alert.severity == 15, Alert.status == "new").scalar()

    # Open Alerts (status != 'done' / 'closed')
    open_alerts = db.query(func.count(Alert.id)).filter(Alert.status.notin_(["done", "closed", "resolved"])).scalar()

    # Open Cases (state != 'closed')
    open_cases = db.query(func.count(Case.id)).filter(Case.state != "closed").scalar()

    return templates.TemplateResponse("dashboard/dashboard_operator.html", {
        "request": request,
        "critical_alerts_count": critical_alerts,
        "open_alerts_count": open_alerts,
        "open_cases_count": open_cases,
    })
