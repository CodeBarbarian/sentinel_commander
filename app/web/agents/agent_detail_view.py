from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.utils import auth
from app.utils.parser.compat_parser_runner import run_parser_for_type
from fastapi.templating import Jinja2Templates
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/agents/{agent_name}", response_class=HTMLResponse)
def agent_detail_view(
    agent_name: str,
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=1000),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    """
    Show all alerts for a given agent (PostgreSQL JSONB safe).
    """
    offset = (page - 1) * limit

    # PostgreSQL: use JSONB extraction instead of SQLite JSON1
    agent_expr = func.lower(
        func.trim(
            func.coalesce(
                func.jsonb_extract_path_text(Alert.source_payload, 'agent', 'name'),
                func.jsonb_extract_path_text(Alert.source_payload, 'agent_name')
            )
        )
    )

    query = (
        db.query(Alert)
        .filter(agent_expr == agent_name.lower())
        .order_by(Alert.created_at.desc())
    )

    total = query.count()
    alerts = query.offset(offset).limit(limit).all()

    for alert in alerts:
        try:
            payload = json.loads(alert.source_payload or "{}")
            parsed = run_parser_for_type("alert", payload)
            alert.parsed_fields = parsed.get("mapped_fields", {})
        except Exception:
            alert.parsed_fields = {}
        alert.created_at_formatted = alert.created_at.strftime("%Y-%m-%d %H:%M:%S") if alert.created_at else "-"

    total_pages = (total // limit) + (1 if total % limit else 0)

    return templates.TemplateResponse("agents/agent_detail_view.html", {
        "request": request,
        "alerts": alerts,
        "agent_name": agent_name,
        "pagination": {
            "page": page,
            "limit": limit,
            "total_results": total,
            "total_pages": total_pages,
            "show_prev": page > 1,
            "show_next": page < total_pages,
            "next_page": page + 1 if page < total_pages else None,
            "prev_page": page - 1 if page > 1 else None,
        }
    })
