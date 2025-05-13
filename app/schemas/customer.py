from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Union, List
from datetime import datetime

class CustomerBase(BaseModel):
    name: str
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    tags: Optional[Union[str, List[str]]] = None


class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    tags: Optional[str] = None
    is_active: Optional[bool] = None

class CustomerResponse(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
