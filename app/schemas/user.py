from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = "analyst"

class UserCreate(UserBase):
    password: str
    is_superuser: Optional[bool] = False
    is_active: Optional[bool] = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
