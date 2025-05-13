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

    # Severity breakdown
    severity_levels = ["Critical", "High", "Medium", "Low", "Info"]
    severity_counts = [
        db.query(func.count(Alert.id)).filter(Alert.severity == level).scalar()
        for level in severity_levels
    ]

    # Alerts per day for last 7 days
    timeline_labels = []
    timeline_values = []
    for i in range(6, -1, -1):
        day = now.date() - timedelta(days=i)
        count = db.query(func.count(Alert.id)).filter(func.date(Alert.created_at) == day).scalar()
        timeline_labels.append(day.strftime("%a"))
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
        recent_alerts.append(alert_dict)

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
        "recent_alerts": recent_alerts
    })
