from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from passlib.hash import bcrypt
from app.core.security import require_admin_api_key
router = APIRouter(dependencies=[Depends(require_admin_api_key)])

@router.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user_data = user.dict()
    user_data["password_hash"] = bcrypt.hash(user_data.pop("password"))

    new_user = User(**user_data)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, update: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = update.dict(exclude_unset=True)

    if "password" in update_data:
        update_data["password_hash"] = bcrypt.hash(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
