from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceOut, SourceUpdate
from typing import List
import uuid
import secrets
from fastapi import Path
from app.core.security import require_admin_api_key

from app.core.security import require_admin_api_key
router = APIRouter(dependencies=[Depends(require_admin_api_key)])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/sources", response_model=SourceOut)
def create_source(source: SourceCreate, db: Session = Depends(get_db), _: None = Depends(require_admin_api_key)):
    generated_guid = str(uuid.uuid4())
    generated_api_key = secrets.token_urlsafe(32)  # Secure random key

    db_source = Source(
        guid=generated_guid,
        name=source.name,
        display_name=source.display_name,
        api_key=generated_api_key,
        is_active=True
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source


@router.get("/sources", response_model=List[SourceOut])
def get_sources(db: Session = Depends(get_db)):
    return db.query(Source).all()

@router.get("/sources/{guid}", response_model=SourceOut)
def get_source(guid: str, db: Session = Depends(get_db), _: None = Depends(require_admin_api_key)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/sources/{guid}/toggle", response_model=SourceOut)
def toggle_source_status(guid: str, db: Session = Depends(get_db), _: None = Depends(require_admin_api_key)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    source.is_active = not source.is_active
    db.commit()
    db.refresh(source)
    return source



@router.delete("/sources/{guid}")
def delete_source(guid: str = Path(...), db: Session = Depends(get_db), _: None = Depends(require_admin_api_key)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.is_protected:
        raise HTTPException(status_code=403, detail="Source is protected and cannot be deleted")

    db.delete(source)
    db.commit()
    return {"status": "deleted", "guid": guid}


@router.patch("/sources/{guid}/regenerate_key", response_model=SourceOut)
def regenerate_api_key(guid: str, db: Session = Depends(get_db), _: None = Depends(require_admin_api_key)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.is_protected:
        raise HTTPException(status_code=403, detail="Source is protected")

    source.api_key = secrets.token_urlsafe(32)
    db.commit()
    db.refresh(source)
    return source

@router.patch("/sources/{guid}", response_model=SourceOut)
def update_source_metadata(guid: str, update: SourceUpdate, db: Session = Depends(get_db), _: None = Depends(require_admin_api_key)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if source.is_protected:
        raise HTTPException(status_code=403, detail="Source is protected and cannot be modified")

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(source, field, value)

    db.commit()
    db.refresh(source)
    return source