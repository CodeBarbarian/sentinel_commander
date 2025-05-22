from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_api_key
from app.models.publisher import PublisherList, PublisherEntry
from app.schemas.publisher import PublisherEntryAPIAdd, PublisherEntryAPIDelete

router = APIRouter()


@router.get("/publisher/{guid}")
def get_publisher_entries(
    guid: str,
    db: Session = Depends(get_db),
    source_auth = Depends(get_api_key)
):
    pub_list = db.query(PublisherList).filter(PublisherList.guid == guid).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")

    entries = db.query(PublisherEntry).filter(PublisherEntry.list_id == pub_list.id).all()
    result = [{"value": e.value, "comment": e.comment, "created_at": e.created_at.isoformat()} for e in entries]
    return JSONResponse(content=result)


@router.post("/publisher/{guid}/add")
def add_publisher_entry(
    guid: str,
    payload: PublisherEntryAPIAdd,
    db: Session = Depends(get_db),
    source_auth = Depends(get_api_key)
):
    pub_list = db.query(PublisherList).filter(PublisherList.guid == guid).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")

    entry = PublisherEntry(
        list_id=pub_list.id,
        value=payload.value.strip(),
        comment=(payload.comment or "").strip(),
        created_at=datetime.utcnow()
    )
    db.add(entry)
    db.commit()
    return {"status": "added", "value": payload.value}


@router.post("/publisher/{guid}/delete")
def delete_publisher_entry(
    guid: str,
    payload: PublisherEntryAPIDelete,
    db: Session = Depends(get_db),
    source_auth = Depends(get_api_key)
):
    pub_list = db.query(PublisherList).filter(PublisherList.guid == guid).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")

    entry = db.query(PublisherEntry).filter(
        PublisherEntry.list_id == pub_list.id,
        PublisherEntry.value == payload.value
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    db.delete(entry)
    db.commit()
    return {"status": "deleted", "value": payload.value}
