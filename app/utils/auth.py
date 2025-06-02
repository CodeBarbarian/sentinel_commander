from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.models.user import User  # adjust if your User model is elsewhere
from app.core.database import get_db

def get_current_user(request: Request, db: Session = Depends(get_db)):
    session_user = request.session.get("user")
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify user exists in DB
    db_user = db.query(User).filter(User.id == session_user.get("id")).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Session invalid or user removed")

    return db_user

def require_admin(request: Request, db: Session = Depends(get_db)):
    session_user = request.session.get("user")
    if not session_user:
        raise HTTPException(status_code=401, detail="Not authenticated")


    db_user = db.query(User).filter(User.id == session_user.get("id")).first()
    if not db_user or db_user.role != "admin":
        raise HTTPException(status_code=401, detail="Not authorized")

    return db_user