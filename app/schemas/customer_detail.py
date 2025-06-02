from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional

class CustomerDetailCreate(BaseModel):
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    sla: Optional[str] = None
    dependencies: Optional[str] = None
    notes: Optional[str] = None

class CustomerDetailOut(CustomerDetailCreate):
    id: int
    customer_id: int

    model_config = ConfigDict(from_attributes=True)