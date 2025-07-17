from typing import List, Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import cast, func, text
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.utils import auth
import json
from app.utils.parser.general_parser_engine import run_parser_for_type
from fastapi.templating import Jinja2Templates
from collections import defaultdict
from sqlalchemy.dialects import postgresql
from sqlalchemy import literal


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def safe_parse_payload(raw):
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        return json.loads(raw or "{}")
    return {}


@router.get("/alerts/category", response_class=HTMLResponse)
def alerts_category_index(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    """
    Show unique alert categories derived from MITRE tactics or fallback to rule.groups[-1].
    Based on active alerts only.
    """

    def safe_parse_payload(raw):
        if isinstance(raw, dict):
            return raw
        if isinstance(raw, str):
            try:
                return json.loads(raw or "{}")
            except json.JSONDecodeError:
                return {}
        return {}

    alerts = db.query(Alert).filter(
        Alert.status.in_(["new", "in_progress"])
    ).all()

    category_counts = defaultdict(int)

    for alert in alerts:
        try:
            payload = safe_parse_payload(alert.source_payload)

            mitre_tactics = payload.get("rule", {}).get("mitre", {}).get("tactic", [])
            if mitre_tactics:
                for tactic in mitre_tactics:
                    category_counts[tactic] += 1
            else:
                groups = payload.get("rule", {}).get("groups", [])
                if groups:
                    category_counts[groups[-1]] += 1

        except Exception as e:
            print(f"Failed to parse alert {alert.id}: {e}")
            continue

    categories = sorted(category_counts.items(), key=lambda item: item[0].lower())

    return templates.TemplateResponse("alerts/category_index.html", {
        "request": request,
        "categories": categories
    })




@router.get("/alerts/category", response_class=HTMLResponse)
def alerts_category_index(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    """
    Show unique alert categories derived from MITRE tactics or fallback to rule.groups[-1].
    Based on active alerts only.
    """
    alerts = db.query(Alert).filter(
        Alert.status.in_(["new", "in_progress"])
    ).all()

    category_counts = defaultdict(int)

    for alert in alerts:
        try:
            if isinstance(alert.source_payload, dict):
                payload = alert.source_payload
            elif isinstance(alert.source_payload, str):
                payload = json.loads(alert.source_payload or "{}")
            else:
                payload = {}

            tactics = payload.get("rule", {}).get("mitre", {}).get("tactic", [])
            # etc...

        except Exception as e:
            print(f"Failed to parse alert {alert.id}: {e}")
            continue

    categories = sorted(category_counts.items(), key=lambda item: item[0])

    return templates.TemplateResponse("alerts/category_index.html", {
        "request": request,
        "categories": categories
    })


@router.get("/alerts/category/{category}/all", response_class=HTMLResponse)
def alerts_by_category_all_view(
    category: str,
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, le=100),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    """
    Show *all* alerts in a given category, regardless of status.
    """

    offset = (page - 1) * page_size

    alerts_query = db.query(Alert).filter(
        func.lower(cast(Alert.source_payload, text)).like(f'%{category.lower()}%')
    )

    total_alerts = alerts_query.count()
    alerts = alerts_query.order_by(
        cast((Alert.status == "done", 1), else_=0),
        Alert.created_at.desc()
    ).offset(offset).limit(page_size).all()

    for a in alerts:
        try:
            payload = json.loads(a.source_payload or "{}")
            parsed = run_parser_for_type("alert", payload)
            a.parsed_agent = (
                parsed.get("mapped_fields", {}).get("agent_name")
                or parsed.get("mapped_fields", {}).get("agent")
                or "—"
            )
            a.parsed_message = parsed.get("mapped_fields", {}).get("message") or a.message
        except Exception:
            a.parsed_agent = "—"
            a.parsed_message = a.message or "—"

    total_pages = max((total_alerts + page_size - 1) // page_size, 1)

    return templates.TemplateResponse("alerts/alerts_by_category.html", {
        "request": request,
        "alerts": alerts,
        "category": category,
        "page": page,
        "page_size": page_size,
        "total": total_alerts,
        "pages": total_pages,
        "show_all": True  # optional flag for template tweaks
    })
