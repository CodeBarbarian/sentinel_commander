from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from app.core.database import get_db
from app.utils import auth
from app.models.publisher import PublisherList, PublisherEntry
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/sentineliq/publisher", response_class=HTMLResponse)
def view_publisher_lists(
        request: Request,
        db: Session = Depends(get_db),
        user=Depends(auth.get_current_user)
):
    lists = db.query(PublisherList).order_by(PublisherList.created_at.desc()).all()
    return templates.TemplateResponse("sentineliq_publisher/sentineliq_publisher.html", {
        "request": request,
        "lists": lists
    })


@router.post("/sentineliq/publisher/create")
def create_list(
        name: str = Form(...),
        list_type: str = Form(...),
        description: str = Form(""),
        db: Session = Depends(get_db),
        user=Depends(auth.get_current_user)
):
    new_list = PublisherList(
        name=name,
        list_type=list_type,
        description=description,
        guid=str(uuid4()),
        created_at=datetime.utcnow()
    )
    db.add(new_list)
    db.commit()
    return RedirectResponse(url="/web/v1/sentineliq/publisher", status_code=303)


@router.get("/sentineliq/publisher/{list_id}/delete")
def delete_list(
        list_id: int,
        db: Session = Depends(get_db),
        user=Depends(auth.get_current_user)
):
    pub_list = db.query(PublisherList).filter(PublisherList.id == list_id).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")
    db.delete(pub_list)
    db.commit()
    return RedirectResponse(url="/web/v1/sentineliq/publisher", status_code=303)


@router.post("/sentineliq/publisher/{list_id}/update")
def update_list(
    list_id: int,
    name: str = Form(...),
    list_type: str = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    pub_list = db.query(PublisherList).filter(PublisherList.id == list_id).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")

    pub_list.name = name.strip()
    pub_list.list_type = list_type.strip()
    pub_list.description = description.strip()

    db.commit()
    return RedirectResponse(url="/web/v1/sentineliq/publisher", status_code=303)


@router.get("/publisher/{guid}", response_class=PlainTextResponse)
def view_public_list(
    guid: str,
    db: Session = Depends(get_db)
):
    pub_list = db.query(PublisherList).filter(PublisherList.guid == guid).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")

    entries = db.query(PublisherEntry).filter(PublisherEntry.list_id == pub_list.id).order_by(PublisherEntry.created_at).all()
    content = "\n".join(entry.value for entry in entries)
    return PlainTextResponse(content)

@router.get("/sentineliq/publisher/{list_id}", response_class=HTMLResponse)
def view_list_entries(
    list_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    pub_list = db.query(PublisherList).filter(PublisherList.id == list_id).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")

    entries = db.query(PublisherEntry).filter(PublisherEntry.list_id == list_id).order_by(PublisherEntry.created_at.desc()).all()

    return templates.TemplateResponse("sentineliq_publisher/sentineliq_publisher_view.html", {
        "request": request,
        "list": pub_list,
        "entries": entries
    })


@router.post("/sentineliq/publisher/{list_id}/entries/add")
def add_entry(
    list_id: int,
    value: str = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    entry = PublisherEntry(
        list_id=list_id,
        value=value.strip(),
        comment=comment.strip(),
        created_at=datetime.utcnow()
    )
    db.add(entry)
    db.commit()
    return RedirectResponse(url=f"/web/v1/sentineliq/publisher/{list_id}", status_code=303)


@router.post("/sentineliq/publisher/{list_id}/entries/{entry_id}/delete")
def delete_entry(
    list_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    entry = db.query(PublisherEntry).filter(PublisherEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return RedirectResponse(url=f"/web/v1/sentineliq/publisher/{list_id}", status_code=303)

@router.post("/sentineliq/publisher/{list_id}/entries/{entry_id}/edit")
def edit_entry(
    list_id: int,
    entry_id: int,
    value: str = Form(...),
    comment: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    entry = db.query(PublisherEntry).filter(PublisherEntry.id == entry_id, PublisherEntry.list_id == list_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    entry.value = value.strip()
    entry.comment = comment.strip()
    db.commit()

    return RedirectResponse(url=f"/web/v1/sentineliq/publisher/{list_id}", status_code=303)
