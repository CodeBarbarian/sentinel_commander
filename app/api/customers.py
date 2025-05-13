from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse
from app.core.security import require_admin_api_key
router = APIRouter(dependencies=[Depends(require_admin_api_key)])

@router.post("/customers", response_model=CustomerResponse)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    data = customer.dict()
    # Handle tags as comma-separated string for DB
    if "tags" in data and isinstance(data["tags"], list):
        data["tags"] = ",".join(data["tags"]) if data["tags"] else None

    db_customer = Customer(**data)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return _format_customer_response(db_customer)


@router.get("/customers", response_model=list[CustomerResponse])
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    return [_format_customer_response(c) for c in customers]


@router.get("/customers/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return _format_customer_response(customer)


@router.put("/customers/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, update: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = update.dict(exclude_unset=True)
    if "tags" in update_data and isinstance(update_data["tags"], list):
        update_data["tags"] = ",".join(update_data["tags"]) if update_data["tags"] else None

    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return _format_customer_response(customer)


@router.delete("/customers/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(customer)
    db.commit()


def _format_customer_response(customer: Customer) -> CustomerResponse:
    tags = customer.tags.split(",") if customer.tags else []
    return CustomerResponse(
        id=customer.id,
        name=customer.name,
        description=customer.description,
        contact_name=customer.contact_name,
        contact_email=customer.contact_email,
        tags=tags,
        is_active=customer.is_active,
        created_at=customer.created_at,
        updated_at=customer.updated_at,
    )
