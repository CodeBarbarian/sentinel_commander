from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer
from datetime import datetime
from app.schemas.alert import AlertCreate, AlertOut, AlertUpdate, AlertBulkActionRequest
from app.models.alert import Alert
from app.core.database import SessionLocal
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from app.models.source import Source
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import status as http_status
from app.utils.parser.runner import run_combined_parser
from app.core.security import get_api_key
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/alerts")
def get_all_alerts(
    db: Session = Depends(get_db),
    source_auth: Source = Depends(get_api_key),
    source: Optional[str] = Query(None),
    severity: Optional[int] = Query(None),
    min_severity: Optional[int] = Query(None),
    severity__in: Optional[List[int]] = Query(None),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    start_event_time: Optional[datetime] = Query(None),
    end_event_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    query = db.query(Alert, Source.display_name).join(Source, Source.id == Alert.source_id, isouter=True)

    # Restrict to the current source's alerts only
    query = query.filter(Alert.source_id == source_auth.id)

    if source:
        query = query.filter(Alert.source == source)
    if min_severity is not None:
        query = query.filter(func.cast(Alert.severity, Integer) >= min_severity)
    if severity__in:
        query = query.filter(func.cast(Alert.severity, Integer).in_(severity__in))

    if status:
        if "," in status:
            query = query.filter(Alert.status.in_(status.split(",")))
        else:
            query = query.filter(Alert.status == status)
    else:
        query = query.filter(Alert.status.in_(["new", "in_progress", "done"]))
    if tags:
        query = query.filter(Alert.tags.ilike(f"%{tags}%"))
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

    total = query.count()

    alerts_raw = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    alerts = []
    for alert, display_name in alerts_raw:
        alert_dict = jsonable_encoder(alert)
        alert_dict["source_display_name"] = display_name

        try:
            alert_payload = json.loads(alert.source_payload)
        except Exception:
            alert_payload = {}

        try:
            parsed = run_combined_parser(alert_payload)
            alert_dict["display_fields"] = []
            for field in parsed.get("display", {}).get("always_show", []):
                path = field.get("field")
                label = field.get("label", path)
                style = field.get("style", "default")
                value = parsed.get("mapped_fields", {}).get(path, "")
                alert_dict["display_fields"].append({
                    "label": label,
                    "value": value,
                    "style": style
                })
        except Exception as e:
            alert_dict["display_fields"] = [{"label": "Parser Error", "value": str(e), "style": "badge"}]

        alerts.append(AlertOut(**alert_dict))

    response_data = {
        "total": total,
        "results": [alert.dict() for alert in alerts]
    }

    return JSONResponse(
        content=jsonable_encoder(response_data),
        status_code=http_status.HTTP_200_OK
    )

@router.get("/alerts/{alert_id}", response_model=AlertOut)
def get_alert_by_id(alert_id: int, db: Session = Depends(get_db), source_auth: Source = Depends(get_api_key)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.source_id == source_auth.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    source = db.query(Source).filter(Source.id == alert.source_id).first()
    display_name = source.display_name if source else "Unknown"

    alert_dict = jsonable_encoder(alert)
    alert_dict["source_display_name"] = display_name

    try:
        alert_dict["source_payload_json"] = json.loads(alert.source_payload)
    except Exception:
        alert_dict["source_payload_json"] = {"error": "Invalid JSON"}

    try:
        parsed = run_combined_parser(alert_dict["source_payload_json"])
        alert_dict["parsed_fields"] = parsed.get("mapped_fields", {})
    except Exception as e:
        alert_dict["parsed_fields"] = {"parser_error": str(e)}

    return AlertOut(**alert_dict)

@router.put("/alerts/{alert_id}", response_model=AlertOut)
def update_alert(alert_id: int, update: AlertUpdate, db: Session = Depends(get_db), source_auth: Source = Depends(get_api_key)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.source_id == source_auth.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(alert, field, value)

    db.commit()
    db.refresh(alert)

    source = db.query(Source).filter(Source.id == alert.source_id).first()
    display_name = source.display_name if source else "Unknown"

    alert_dict = jsonable_encoder(alert)
    alert_dict["source_display_name"] = display_name
    return AlertOut(**alert_dict)

@router.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db), source_auth: Source = Depends(get_api_key)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.source_id == source_auth.id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    db.delete(alert)
    db.commit()
    return {"status": "deleted", "id": alert_id}

@router.post("/alerts/bulk_action")
def bulk_alert_action(payload: AlertBulkActionRequest, db: Session = Depends(get_db), source_auth: Source = Depends(get_api_key)):
    alerts = db.query(Alert).filter(Alert.id.in_(payload.alert_ids), Alert.source_id == source_auth.id).all()

    if not alerts:
        raise HTTPException(status_code=404, detail="No matching alerts found.")

    if payload.action == "delete":
        for alert in alerts:
            db.delete(alert)
        db.commit()
        return {"status": "deleted", "count": len(alerts)}

    elif payload.action == "update":
        if not payload.fields:
            raise HTTPException(status_code=400, detail="Missing update fields for bulk update.")

        allowed_fields = {"status", "resolution", "resolution_comment", "tags", "severity"}
        for alert in alerts:
            for key, value in payload.fields.items():
                if key in allowed_fields:
                    setattr(alert, key, value)
        db.commit()
        return {"status": "updated", "count": len(alerts)}

    else:
        raise HTTPException(status_code=400, detail="Invalid action type.")
