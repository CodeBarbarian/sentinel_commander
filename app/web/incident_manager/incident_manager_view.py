from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.utils import auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/incident/list", response_class=HTMLResponse)
def incident_view(request: Request, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse("incident_manager/list.html", {
        "request": request,
    })

@router.get("/incident/1", response_class=HTMLResponse)
def incident_detail_view(request: Request, user=Depends(auth.get_current_user), db: Session = Depends(get_db)):
    return templates.TemplateResponse("incident_manager/incident_detail.html", {
        "request": request,
    })