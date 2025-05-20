from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.utils import auth
from app.models.alert import Alert
from app.models.case import Case
from app.models.customer import Customer
from app.models.assets import Asset
from app.models.iocs import IOC
from app.utils.parser.compat_parser_runner import run_parser_for_type
from fastapi.templating import Jinja2Templates
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/sentineliq/search", response_class=HTMLResponse)
def sentineliq_search(
    request: Request,
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    results = []
    query = q.lower()

    # === ALERTS ===
    alerts = db.query(Alert).filter(
        or_(
            Alert.message.ilike(f"%{query}%"),
            Alert.tags.ilike(f"%{query}%"),
            Alert.source.ilike(f"%{query}%")
        )
    ).limit(20).all()

    for alert in alerts:
        try:
            parsed = json.loads(alert.source_payload or "{}")
            fields = run_parser_for_type("alert", parsed).get("mapped_fields", {})
        except Exception:
            fields = {}

        parsed_hit = next(
            (f"{k}: {v}" for k, v in fields.items() if query in str(v).lower()),
            None
        )

        results.append({
            "type": "alert",
            "id": alert.id,
            "title": alert.message[:60],
            "match": parsed_hit or f"message: {alert.message[:60]}"
        })

    # === CASES ===
    cases = db.query(Case).filter(
        or_(
            Case.title.ilike(f"%{query}%"),
            Case.description.ilike(f"%{query}%"),
            Case.classification.ilike(f"%{query}%"),
            Case.state.ilike(f"%{query}%")
        )
    ).limit(20).all()

    for case in cases:
        results.append({
            "type": "case",
            "id": case.id,
            "title": case.title,
            "match": f"state: {case.state}"
        })

    # === CUSTOMERS ===
    customers = db.query(Customer).filter(
        or_(
            Customer.name.ilike(f"%{query}%"),
            Customer.description.ilike(f"%{query}%"),
            Customer.contact_name.ilike(f"%{query}%"),
            Customer.tags.ilike(f"%{query}%")
        )
    ).limit(20).all()

    for customer in customers:
        results.append({
            "type": "customer",
            "id": customer.id,
            "title": customer.name,
            "match": "customer match"
        })

    # === ASSETS ===
    assets = db.query(Asset).filter(
        or_(
            Asset.hostname.ilike(f"%{query}%"),
            Asset.ip_address.ilike(f"%{query}%"),
            Asset.name.ilike(f"%{query}%"),
            Asset.notes.ilike(f"%{query}%"),
            Asset.tags.ilike(f"%{query}%"),
            Asset.type.ilike(f"%{query}%")
        )
    ).limit(20).all()

    for asset in assets:
        results.append({
            "type": "asset",
            "id": asset.id,
            "title": asset.hostname or asset.name or asset.ip_address,
            "match": "asset match"
        })

    # === IOCs ===
    iocs = db.query(IOC).filter(
        or_(
            IOC.value.ilike(f"%{query}%"),
            IOC.description.ilike(f"%{query}%"),
            IOC.tags.ilike(f"%{query}%"),
            IOC.source.ilike(f"%{query}%")
        )
    ).limit(20).all()

    for ioc in iocs:
        results.append({
            "type": "ioc",
            "id": ioc.id,
            "title": ioc.value,
            "match": f"type: {ioc.type}"
        })

    return templates.TemplateResponse("sentineliq_search/sentineliq_search.html", {
        "request": request,
        "query": q,
        "results": results
    })