from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.alert import Alert
from app.utils import auth
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, text

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

from sqlalchemy import func, text

@router.get("/agents", response_class=HTMLResponse)
def agent_list_view(
    request: Request,
    q: str = Query(None, description="Search by agent name"),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    """
    PostgreSQL JSONB: extract agent ID, NAME, IP from `source_payload` with correct paths.
    """
    agent_id_expr = func.jsonb_extract_path_text(Alert.source_payload, 'agent', 'id').label("agent_id")
    agent_name_expr = func.jsonb_extract_path_text(Alert.source_payload, 'agent', 'name').label("agent_name")
    agent_ip_expr = func.jsonb_extract_path_text(Alert.source_payload, 'agent', 'ip').label("agent_ip")

    agents_query = (
        db.query(
            agent_id_expr,
            agent_name_expr,
            agent_ip_expr,
            func.count(Alert.id).label("total_alerts"),
            func.max(Alert.created_at).label("last_alert_time")
        )
        .filter(Alert.source_payload != None)
        .filter(agent_name_expr.isnot(None))
        .group_by(agent_id_expr, agent_name_expr, agent_ip_expr)
        .order_by(func.max(Alert.created_at).desc())
    )

    agent_rows = agents_query.all()

    agents = []
    for row in agent_rows:
        agents.append({
            "id": row.agent_id or "-",
            "name": row.agent_name or "-",
            "ip": row.agent_ip or "-",
            "total_alerts": row.total_alerts,
            "last_alert_time": row.last_alert_time
        })

    return templates.TemplateResponse("agents/agent_view.html", {
        "request": request,
        "agents": agents,
        "search_query": q or ""
    })


