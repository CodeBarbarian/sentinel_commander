from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path
import markdown2

from app.utils import auth
from app.core.database import get_db
from app.models.module import Module

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
DOCS_DIR = Path("app/docs")


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


@router.get("/docs", response_class=HTMLResponse)
async def docs_index(request: Request):
    md_file = DOCS_DIR / "index.md"
    if not md_file.exists():
        raise HTTPException(status_code=404, detail="index.md not found")

    html_content = markdown2.markdown(md_file.read_text(encoding="utf-8"), extras=["fenced-code-blocks", "tables"])
    return templates.TemplateResponse("docs/doc_template.html", {
        "request": request,
        "content": html_content,
        "section": "index",
        "page": "index"
    })

@router.get("/docs/{section}/{page}", response_class=HTMLResponse)
async def docs_page(request: Request, section: str, page: str):
    md_file = DOCS_DIR / section / f"{page}.md"
    if not md_file.exists():
        raise HTTPException(status_code=404, detail="Documentation page not found.")

    html_content = markdown2.markdown(md_file.read_text(encoding="utf-8"), extras=["fenced-code-blocks", "tables"])
    return templates.TemplateResponse("docs/doc_template.html", {
        "request": request,
        "content": html_content,
        "section": section,
        "page": page
    })