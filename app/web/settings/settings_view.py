from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.utils import auth
from app.core.database import get_db
from app.models.module import Module  # Ensure this model is defined and imported
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user=Depends(auth.get_current_user)):
    return templates.TemplateResponse("settings/settings.html", {"request": request})


@router.get("/settings/parser-sandbox", response_class=HTMLResponse)
async def parser_sandbox_view(request: Request, user=Depends(auth.get_current_user)):
    return templates.TemplateResponse("settings/parser_sandbox.html", {"request": request})


@router.get("/settings/modules", response_class=HTMLResponse)
async def modules_page(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    modules = db.query(Module).all()
    return templates.TemplateResponse("modules/modules.html", {
        "request": request,
        "modules": modules
    })