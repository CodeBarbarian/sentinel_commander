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
from app.models.publisher import PublisherList, PublisherEntry
from app.utils.parser.compat_parser_runner import run_parser_for_type
from fastapi.templating import Jinja2Templates
import json
from datetime import datetime
import re

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def parse_query_terms(q: str):
    kv_pattern = re.compile(r'(\w+):"([^"]+)"|(\w+):([^\s]+)')
    kv_matches = kv_pattern.findall(q)

    kv_terms = []
    for m in kv_matches:
        key = m[0] or m[2]
        value = m[1] or m[3]
        kv_terms.append((key.lower(), value.lower()))

    # Remove matched patterns from original query to extract free terms
    q_clean = kv_pattern.sub('', q)
    free_terms = [t.strip().lower() for t in q_clean.strip().split() if t.strip()]

    return kv_terms, free_terms

def flatten_json(y, prefix=''):
    """Flatten nested JSON, returning (key_path, value) pairs."""
    out = []
    for k, v in y.items():
        new_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.extend(flatten_json(v, new_key))
        elif isinstance(v, list):
            for idx, item in enumerate(v):
                out.append((f"{new_key}[{idx}]", item))
        else:
            out.append((new_key, v))
    return out

@router.get("/sentineliq/search", response_class=HTMLResponse)
def sentineliq_search(
    request: Request,
    q: str = Query(..., min_length=2),
    type: str = Query(default=None),
    tags: str = Query(default=None),
    start: str = Query(default=None),
    end: str = Query(default=None),
    limit: int = Query(default=None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    results = []
    query = q.lower()
    kv_terms, free_terms = parse_query_terms(q)

    # Convert date filters if present
    start_dt = None
    end_dt = None
    try:
        if start:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
        if end:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
    except Exception:
        pass  # Ignore invalid date formats

    tags_list = [t.strip().lower() for t in tags.split(",")] if tags else []

    # === ALERTS ===
    if not type or type == "alert":
        alerts_query = db.query(Alert)
        alerts = alerts_query.limit(limit or 100).all()
        for alert in alerts:
            match_field = None
            try:
                parsed_payload = json.loads(alert.source_payload or "{}")
            except Exception:
                parsed_payload = {}

            flat_fields = flatten_json(parsed_payload)
            try:
                parsed_fields = run_parser_for_type("alert", parsed_payload).get("mapped_fields", {})
            except Exception:
                parsed_fields = {}

            # Combine mapped + flattened fields
            combined_fields = {str(k).lower(): str(v).lower() for k, v in parsed_fields.items()}
            for k, v in flat_fields:
                combined_fields[str(k).lower()] = str(v).lower()

            # Match logic: ALL key:value pairs must match
            kv_matches = all(
                any(kv_key in field_k and kv_val in field_v for field_k, field_v in combined_fields.items())
                for kv_key, kv_val in kv_terms
            )

            # If no kv_terms, allow
            if not kv_terms:
                kv_matches = True

            # Free-term match (if any)
            free_matches = True
            if free_terms:
                free_matches = any(
                    term in field_k or term in field_v
                    for term in free_terms
                    for field_k, field_v in combined_fields.items()
                )

            if kv_matches and free_matches:
                match_field = next(
                    (f"{k}: {v}" for k, v in combined_fields.items()
                     if any(kv[0] in k and kv[1] in v for kv in kv_terms) or
                     any(t in k or t in v for t in free_terms)),
                    None
                )

                if tags_list and not any(tag in (alert.tags or "").lower() for tag in tags_list):
                    continue

                results.append({
                    "type": "alert",
                    "id": alert.id,
                    "title": alert.message[:60] or "Alert",
                    "match": f"[payload] {match_field or 'Matched'}"
                })

    # === CASES ===
    if not type or type == "case":
        cases = db.query(Case).filter(
            or_(
                Case.title.ilike(f"%{query}%"),
                Case.description.ilike(f"%{query}%"),
                Case.classification.ilike(f"%{query}%"),
                Case.state.ilike(f"%{query}%")
            )
        ).limit(limit or 20).all()
        for case in cases:
            results.append({
                "type": "case",
                "id": case.id,
                "title": case.title,
                "match": f"state: {case.state}"
            })

    # === CUSTOMERS ===
    if not type or type == "customer":
        customers = db.query(Customer).filter(
            or_(
                Customer.name.ilike(f"%{query}%"),
                Customer.description.ilike(f"%{query}%"),
                Customer.contact_name.ilike(f"%{query}%"),
                Customer.tags.ilike(f"%{query}%")
            )
        ).limit(limit or 20).all()
        for customer in customers:
            results.append({
                "type": "customer",
                "id": customer.id,
                "title": customer.name,
                "match": "customer match"
            })

    # === ASSETS ===
    if not type or type == "asset":
        assets = db.query(Asset).filter(
            or_(
                Asset.hostname.ilike(f"%{query}%"),
                Asset.ip_address.ilike(f"%{query}%"),
                Asset.name.ilike(f"%{query}%"),
                Asset.notes.ilike(f"%{query}%"),
                Asset.tags.ilike(f"%{query}%"),
                Asset.type.ilike(f"%{query}%")
            )
        ).limit(limit or 20).all()
        for asset in assets:
            results.append({
                "type": "asset",
                "id": asset.id,
                "title": asset.hostname or asset.name or asset.ip_address,
                "match": "asset match"
            })

    # === IOCs ===
    if not type or type == "ioc":
        iocs = db.query(IOC).filter(
            or_(
                IOC.value.ilike(f"%{query}%"),
                IOC.description.ilike(f"%{query}%"),
                IOC.tags.ilike(f"%{query}%"),
                IOC.source.ilike(f"%{query}%")
            )
        ).limit(limit or 20).all()
        for ioc in iocs:
            results.append({
                "type": "ioc",
                "id": ioc.id,
                "title": ioc.value,
                "match": f"type: {ioc.type}"
            })

    # === PUBLISHER LISTS ===
    if not type or type == "publisher_list":
        lists = db.query(PublisherList).filter(
            or_(
                PublisherList.name.ilike(f"%{query}%"),
                PublisherList.description.ilike(f"%{query}%"),
                PublisherList.guid.ilike(f"%{query}%")
            )
        ).limit(limit or 20).all()
        for pub_list in lists:
            results.append({
                "type": "publisher_list",
                "id": pub_list.id,
                "title": pub_list.name,
                "match": f"GUID: {pub_list.guid}"
            })

    # === PUBLISHER ENTRIES ===
    if not type or type == "publisher_entry":
        entries = db.query(PublisherEntry).filter(
            or_(
                PublisherEntry.value.ilike(f"%{query}%"),
                PublisherEntry.comment.ilike(f"%{query}%")
            )
        ).limit(limit or 20).all()
        for entry in entries:
            results.append({
                "type": "publisher_entry",
                "id": entry.id,
                "list_id": entry.list_id,
                "title": entry.value[:80],
                "match": f"comment: {entry.comment or '—'}"
            })

    return templates.TemplateResponse("sentineliq_search/sentineliq_search.html", {
        "request": request,
        "query": q,
        "results": results
    })

@router.get("/sentineliq/search/advanced", response_class=HTMLResponse)
def sentineliq_advanced_search(request: Request, user=Depends(auth.get_current_user)):
    return templates.TemplateResponse("sentineliq_search/sentineliq_search_advanced.html", {
        "request": request
    })