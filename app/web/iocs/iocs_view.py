# app/web/iocs/iocs_view.py
from typing import Optional

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.iocs import IOC
from fastapi.templating import Jinja2Templates
from app.utils import auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/iocs", response_class=HTMLResponse)
def list_iocs(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    iocs = db.query(IOC).order_by(IOC.created_at.desc()).all()
    return templates.TemplateResponse("iocs/iocs.html", {"request": request, "iocs": iocs})

@router.post("/iocs/create")
def create_ioc(
    type: str = Form(...),
    value: str = Form(...),
    description: str = Form(None),
    source: str = Form(None),
    tags: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    ioc = IOC(type=type, value=value, description=description, source=source, tags=tags)
    db.add(ioc)
    db.commit()
    return RedirectResponse("/web/v1/iocs", status_code=302)

@router.post("/iocs/delete")
def delete_ioc(ioc_id: int = Form(...), db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    ioc = db.query(IOC).filter(IOC.id == ioc_id).first()
    if ioc:
        db.delete(ioc)
        db.commit()
    return RedirectResponse("/web/v1/iocs", status_code=302)

@router.post("/iocs/edit")
def edit_ioc(
    ioc_id: int = Form(...),
    type: str = Form(...),
    value: str = Form(...),
    description: str = Form(None),
    source: str = Form(None),
    tags: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    ioc = db.query(IOC).filter(IOC.id == ioc_id).first()
    if ioc:
        ioc.type = type
        ioc.value = value
        ioc.description = description
        ioc.source = source
        ioc.tags = tags
        db.commit()
    return RedirectResponse("/web/v1/iocs", status_code=302)

@router.get("/iocs/{ioc_id}", response_class=HTMLResponse)
def ioc_detail_view(
    request: Request,
    ioc_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    ioc = db.query(IOC).filter(IOC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")

    def serialize_ioc(i):
        return {
            "id": i.id,
            "type": i.type,
            "value": i.value,
            "description": i.description,
            "source": i.source,
            "tags": i.tags,
        }

    return templates.TemplateResponse("iocs/iocs_detail.html", {
        "request": request,
        "ioc": ioc,
        "ioc_json": serialize_ioc(ioc)
    })

@router.post("/iocs/{ioc_id}/edit")
def update_ioc(
    ioc_id: int,
    type: str = Form(...),
    value: str = Form(...),
    source: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    ioc = db.query(IOC).filter(IOC.id == ioc_id).first()
    if not ioc:
        raise HTTPException(status_code=404, detail="IOC not found")

    ioc.type = type.strip()
    ioc.value = value.strip()
    ioc.source = source
    ioc.tags = tags
    ioc.description = description

    db.commit()
    return RedirectResponse(url=f"/web/v1/iocs/{ioc_id}", status_code=303)
