from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.utils import auth
from app.models.alert import Alert
from app.models.customer import Customer
from app.models.assets import Asset
from app.models.iocs import IOC
from app.models.publisher import PublisherList, PublisherEntry
from app.utils.parser.compat_parser_runner import run_parser_for_type
from fastapi.templating import Jinja2Templates
import json
from datetime import datetime
import re
from app.models.saved_search import SavedSearch
from fastapi import Form
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def parse_query_terms(q: str):
    """
    Parse 'key:value' pairs and free terms.
    Supports quoted values: e.g., user:"John Doe"
    """
    kv_pattern = re.compile(r'(\w+):"([^"]+)"|(\w+):([^\s]+)')
    kv_matches = kv_pattern.findall(q)

    kv_terms = []
    for m in kv_matches:
        key = m[0] or m[2]
        value = m[1] or m[3]
        kv_terms.append((key.lower(), value.lower()))

    q_clean = kv_pattern.sub('', q)
    free_terms = [t.strip().lower() for t in q_clean.strip().split() if t.strip()]

    return kv_terms, free_terms


def flatten_json(y, prefix=''):
    """
    Recursively flatten a nested dict/list JSON.
    Returns list of (key_path, value) pairs.
    """
    out = []
    if isinstance(y, dict):
        for k, v in y.items():
            new_key = f"{prefix}.{k}" if prefix else k
            out.extend(flatten_json(v, new_key))
    elif isinstance(y, list):
        for idx, item in enumerate(y):
            new_key = f"{prefix}[{idx}]"
            out.extend(flatten_json(item, new_key))
    else:
        out.append((prefix, y))
    return out


def match_with_wildcard(value: str, term: str) -> bool:
    """
    Supports simple * and ? wildcards.
    """
    pattern = '^' + re.escape(term).replace(r'\*', '.*').replace(r'\?', '.') + '$'
    return re.match(pattern, value) is not None


def unified_match(combined_fields, kv_terms, free_terms):
    """
    True if all kv_terms AND free_terms match against the combined flattened fields.
    """
    # Match kv terms
    kv_matches = all(
        any(
            match_with_wildcard(field_k, kv_key) and match_with_wildcard(field_v, kv_val)
            for field_k, field_v in combined_fields.items()
        )
        for kv_key, kv_val in kv_terms
    ) if kv_terms else True

    # Match free terms
    free_matches = all(
        any(
            match_with_wildcard(field_k, term) or match_with_wildcard(field_v, term)
            for field_k, field_v in combined_fields.items()
        )
        for term in free_terms
    ) if free_terms else True

    return kv_matches and free_matches


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

    start_dt, end_dt = None, None
    try:
        if start:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
        if end:
            end_dt = datetime.strptime(end, "%Y-%m-%d")
    except Exception:
        pass

    tags_list = [t.strip().lower() for t in tags.split(",")] if tags else []

    # === ALERTS ===
    if not type or type == "alert":
        alerts_query = db.query(Alert)
        alerts = alerts_query.limit(limit or 100).all()
        for alert in alerts:
            try:
                parsed_payload = json.loads(alert.source_payload or "{}")
            except Exception:
                parsed_payload = {}

            try:
                parsed_fields = run_parser_for_type("alert", parsed_payload).get("mapped_fields", {})
            except Exception:
                parsed_fields = {}

            # Flatten + combine
            flat_fields = flatten_json(parsed_payload)
            combined_fields = {str(k).lower(): str(v).lower() for k, v in parsed_fields.items()}
            for k, v in flat_fields:
                combined_fields[k.lower()] = str(v).lower()

            # Inject direct agent if you have one in the DB
            if getattr(alert, "agent_name", None):
                combined_fields["agent.name"] = alert.agent_name.lower()

            # Also ensure basic fields like message/tags are always included
            combined_fields["message"] = (alert.message or "").lower()
            combined_fields["tags"] = (alert.tags or "").lower()

            if unified_match(combined_fields, kv_terms, free_terms):
                if tags_list and not any(tag in combined_fields["tags"] for tag in tags_list):
                    continue

                results.append({
                    "type": "alert",
                    "id": alert.id,
                    "title": alert.message[:60] or "Alert",
                    "match": "Matched in alert payload"
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
def sentineliq_advanced_search(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    saved_searches = db.query(SavedSearch).order_by(SavedSearch.created_at.desc()).limit(20).all()
    return templates.TemplateResponse("sentineliq_search/sentineliq_search_advanced.html", {
        "request": request,
        "saved_searches": saved_searches
    })

@router.post("/sentineliq/save_search", response_class=HTMLResponse)
def save_search(
    name: str = Form(...),
    query_string: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    db.add(SavedSearch(name=name, query_string=query_string))
    db.commit()
    return HTMLResponse('<script>window.location.href="/web/v1/sentineliq/search/advanced";</script>')

from fastapi.responses import JSONResponse

@router.delete("/sentineliq/search/saved/{search_id}")
def delete_saved_search(
    search_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    saved = db.query(SavedSearch).filter(SavedSearch.id == search_id).first()
    if not saved:
        return JSONResponse(status_code=404, content={"detail": "Search not found"})
    db.delete(saved)
    db.commit()
    return {"status": "deleted"}