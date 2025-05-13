from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.source import Source
from app.models.alert import Alert
from app.schemas.alert import AlertCreate
from datetime import datetime
from typing import Optional
import uuid

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/webhook/{guid}")
def receive_alert(guid: str, payload: AlertCreate, request: Request, db: Session = Depends(get_db)):
    # 1. Validate Source by GUID and API Key
    source = db.query(Source).filter(Source.guid == guid).first()
    if not source or not source.is_active:
        raise HTTPException(status_code=403, detail="Invalid or inactive source")

    # 2. Authorization check
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.split(" ")[1]
    if token != source.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    # 3. Deduplication check
    existing_alert = None
    if payload.source_ref_id:
        existing_alert = db.query(Alert).filter(
            Alert.source_ref_id == payload.source_ref_id,
            Alert.source_id == source.id
        ).first()

    if existing_alert:
        has_changes = False
        for field in [
            "message", "severity", "observables", "status",
            "tags", "source_event_time", "source_payload"
        ]:
            new_value = getattr(payload, field)
            old_value = getattr(existing_alert, field)
            if new_value != old_value:
                setattr(existing_alert, field, new_value)
                has_changes = True

        if has_changes:
            db.commit()
            db.refresh(existing_alert)
            return {"status": "updated", "id": existing_alert.id}
        else:
            return {"status": "duplicate", "id": existing_alert.id}

    # 4. Create new alert
    new_alert = Alert(
        source_id=source.id,
        source=payload.source,
        source_ref_id=payload.source_ref_id or str(uuid.uuid4()),
        severity=payload.severity,
        message=payload.message,
        observables=payload.observables,
        status=payload.status or "new",
        tags=payload.tags or "",
        source_event_time=payload.source_event_time or datetime.now(),
        source_payload=payload.source_payload,
    )

    db.add(new_alert)
    db.commit()
    db.refresh(new_alert)

    return {"status": "created", "id": new_alert.id}
