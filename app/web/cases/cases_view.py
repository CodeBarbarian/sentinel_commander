# app/web/cases_view.py
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.params import Form
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from app.core.database import get_db
from app.models import Customer, User, CaseTag
from app.models.case import Case
from fastapi.templating import Jinja2Templates
from app.utils import auth
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/cases", response_class=HTMLResponse)
def list_cases(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return templates.TemplateResponse("cases/cases.html", {"request": request, "cases": cases})

@router.get("/cases/new", response_class=HTMLResponse)
def new_case_page(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    customers = db.query(Customer).all()
    users = db.query(User).all()
    return templates.TemplateResponse("cases/cases_create.html", {
        "request": request,
        "customers": customers,
        "users": users,
    })


@router.post("/cases/create")
def create_case(
    title: str = Form(...),
    description: str = Form(""),
    severity: str = Form(...),
    classification: str = Form(""),
    tags: str = Form(""),
    customer_id: int = Form(...),
    assigned_to: Optional[str] = Form(None),
    state: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    assigned_id = int(assigned_to) if assigned_to else None
    new_case = Case(
        title=title,
        description=description,
        severity=severity,
        classification=classification,
        customer_id=customer_id,
        assigned_to=assigned_id,
        state=state,
    )

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    new_case.tags = [CaseTag(tag=tag) for tag in tag_list]

    db.add(new_case)
    db.commit()

    return RedirectResponse(url=f"/web/v1/cases/{new_case.id}", status_code=303)
