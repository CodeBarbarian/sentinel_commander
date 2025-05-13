from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.utils import auth
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request, user=Depends(auth.get_current_user)):
    return templates.TemplateResponse("sources/sources.html", {"request": request})
