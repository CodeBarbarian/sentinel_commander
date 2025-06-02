from fastapi import APIRouter, Request, Form, Depends, HTTPException
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
def user_list(request: Request, db: Session = Depends(get_db), user=Depends(auth.require_admin)):
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
    user=Depends(auth.require_admin)
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
    current_user=Depends(auth.require_admin)
):
    # Ensure current_user is a real model, not a dict
    if isinstance(current_user, dict):
        current_user = db.query(User).filter(User.id == current_user.get("id")).first()

    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting self
    if current_user.id == user_to_delete.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own user")

    # Count other admin accounts
    admin_count = db.query(User).filter(User.role == "admin", User.id != user_to_delete.id).count()

    if user_to_delete.role == "admin" and admin_count == 0:
        raise HTTPException(status_code=400, detail="You cannot delete the last admin user")

    db.delete(user_to_delete)
    db.commit()
    return RedirectResponse("/web/v1/users", status_code=302)

@router.post("/users/{user_id}/update")
def update_user(
    user_id: int,
    password: str = Form(None),
    role: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user),
):
    # If current_user is a dict, fetch real user from DB
    if isinstance(current_user, dict):
        current_user = db.query(User).filter(User.id == current_user.get("id")).first()

    if not current_user or current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    if password:
        target_user.password_hash = bcrypt.hash(password)

    target_user.role = role
    db.commit()

    return RedirectResponse("/web/v1/users", status_code=302)

@router.get("/users/profile", response_class=HTMLResponse)
def user_profile(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    db_user = db.query(User).filter(User.id == user.id).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return templates.TemplateResponse("users/profile.html", {
        "request": request,
        "user": db_user
    })

@router.post("/profile/update", response_class=HTMLResponse)
def update_profile(
    request: Request,
    full_name: str = Form(None),
    email: str = Form(None),
    password: str = Form(None),
    db: Session = Depends(get_db),
    current_user=Depends(auth.get_current_user)
):
    db_user = db.query(User).filter(User.id == current_user["id"]).first()

    if full_name is not None:
        db_user.full_name = full_name
    if email is not None:
        db_user.email = email
    if password:
        db_user.password_hash = bcrypt.hash(password)

    db.commit()
    db.refresh(db_user)

    return RedirectResponse("/web/v1/profile", status_code=302)