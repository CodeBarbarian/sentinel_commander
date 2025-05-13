from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.utils import auth
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/settings", response_class=HTMLResponse)
async def sources_page(request: Request, user=Depends(auth.get_current_user)):
    return templates.TemplateResponse("settings/settings.html", {"request": request})

@router.get("/settings/parser-sandbox", response_class=HTMLResponse)
async def parser_sandbox_view(request: Request, user=Depends(auth.get_current_user)):
    return templates.TemplateResponse("settings/parser_sandbox.html", {"request": request})
