from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from passlib.hash import bcrypt
from fastapi.templating import Jinja2Templates
from app.utils import auth
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/users", response_class=HTMLResponse)
def user_list(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    users = db.query(User).all()
    return templates.TemplateResponse("users/users.html", {
        "request": request,
        "users": users
    })


@router.post("/users/create")
def create_user(
    request: Request,
    username: str = Form(...),
    full_name: str = Form(None),
    email: str = Form(None),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    hashed_password = bcrypt.hash(password)

    user = User(
        username=username,
        full_name=full_name,
        email=email,
        password_hash=hashed_password,
        role=role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return RedirectResponse("/web/v1/users", status_code=302)


@router.post("/users/delete")
def delete_user(
    user_id: int = Form(...),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return RedirectResponse("/web/v1/users", status_code=302)
