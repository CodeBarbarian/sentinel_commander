from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.source import Source
from app.utils import auth
import uuid
import secrets

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def generate_api_key() -> str:
    return secrets.token_hex(20)


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    sources = db.query(Source).order_by(Source.created_at.desc()).all()
    return templates.TemplateResponse("sources/sources.html", {
        "request": request,
        "sources": sources
    })


@router.post("/sources/create")
async def create_source(
    request: Request,
    name: str = Form(...),
    display_name: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    existing = db.query(Source).filter(Source.name == name).first()
    if existing:
        return RedirectResponse("/web/v1/sources?error=name_exists", status_code=303)

    source = Source(
        name=name,
        display_name=display_name,
        api_key=generate_api_key(),
        guid=str(uuid.uuid4()),
        is_active=True,
        is_protected=False
    )
    db.add(source)
    db.commit()
    return RedirectResponse("/web/v1/sources", status_code=303)


@router.post("/sources/{guid}/toggle")
async def toggle_source(guid: str, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if source:
        source.is_active = not source.is_active
        db.commit()
    return RedirectResponse("/web/v1/sources", status_code=303)


@router.post("/sources/{guid}/regenerate")
async def regenerate_api_key(guid: str, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if source:
        source.api_key = generate_api_key()
        db.commit()
    return RedirectResponse("/web/v1/sources", status_code=303)


@router.post("/sources/{guid}/delete")
async def delete_source(guid: str, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    source = db.query(Source).filter(Source.guid == guid).first()
    if source and not source.is_protected:
        db.delete(source)
        db.commit()
    return RedirectResponse("/web/v1/sources", status_code=303)
