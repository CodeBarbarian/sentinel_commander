from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from passlib.hash import bcrypt
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
@router.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/web/v1/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.post("/login")
def login(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not bcrypt.verify(password, user.password_hash):
        return templates.TemplateResponse("auth/login.html", {
            "request": request,
            "error": "Invalid credentials"
        })

    request.session["user"] = {
        "id": user.id,
        "username": user.username,
        "role": user.role
    }

    return RedirectResponse("/web/v1/dashboard", status_code=302)

@router.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/web/v1/login", status_code=302)
