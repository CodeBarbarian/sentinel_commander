from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

from app.core.database import get_db
from app.utils import auth
from app.models.publisher import PublisherList
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


@router.get("/sentineliq/publisher/{list_id}/edit", response_class=HTMLResponse)
def edit_list_page(
        list_id: int,
        request: Request,
        db: Session = Depends(get_db),
        user=Depends(auth.get_current_user)
):
    pub_list = db.query(PublisherList).filter(PublisherList.id == list_id).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")
    return templates.TemplateResponse("sentineliq_publisher/publisher_edit.html", {
        "request": request,
        "list": pub_list
    })

@router.get("/sentineliq/publisher/{guid}", response_class=HTMLResponse)
def view_public_list(
    guid: str,
    request: Request,
    db: Session = Depends(get_db)
):
    pub_list = db.query(PublisherList).filter(PublisherList.guid == guid).first()
    if not pub_list:
        raise HTTPException(status_code=404, detail="List not found")

    return templates.TemplateResponse("sentineliq_publisher/sentineliq_publisher_public.html", {
        "request": request,
        "list": pub_list
    })