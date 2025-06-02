from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.core.database import get_db
from app.utils import auth
from fastapi.templating import Jinja2Templates
from app.models.customer_detail import CustomerDetail
from app.schemas.customer_detail import CustomerDetailCreate

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/customers", response_class=HTMLResponse)
def list_customers(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    customers = db.query(Customer).all()
    return templates.TemplateResponse("customers/customers.html", {"request": request, "customers": customers})

@router.post("/customers/create")
def create_customer(name: str = Form(...), description: str = Form(None), db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    customer = Customer(name=name.strip(), description=description)
    db.add(customer)
    db.commit()
    return RedirectResponse("/web/v1/customers", status_code=302)

@router.post("/customers/delete")
def delete_customer(customer_id: int = Form(...), db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        db.delete(customer)
        db.commit()
    return RedirectResponse("/web/v1/customers", status_code=302)

@router.post("/customers/edit")
def edit_customer(
    customer_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.name = name.strip()
        customer.description = description.strip() if description else None
        db.commit()
    return RedirectResponse("/web/v1/customers", status_code=302)

@router.get("/customers/{customer_id}", response_class=HTMLResponse)
def customer_detail_view(customer_id: int, request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    detail = db.query(CustomerDetail).filter(CustomerDetail.customer_id == customer.id).first()
    return templates.TemplateResponse("customers/customer_detail.html", {
        "request": request,
        "customer": customer,
        "detail": detail
    })

@router.post("/customers/{customer_id}/details")
def update_customer_details(
    customer_id: int,
    request: Request,
    contact_name: str = Form(None),
    contact_email: str = Form(None),
    contact_phone: str = Form(None),
    address: str = Form(None),
    sla: str = Form(None),
    dependencies: str = Form(None),
    notes: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    detail = db.query(CustomerDetail).filter(CustomerDetail.customer_id == customer_id).first()
    if not detail:
        detail = CustomerDetail(customer_id=customer_id)
        db.add(detail)

    detail.contact_name = contact_name
    detail.contact_email = contact_email
    detail.contact_phone = contact_phone
    detail.address = address
    detail.sla = sla
    detail.dependencies = dependencies
    detail.notes = notes

    db.commit()
    return RedirectResponse(f"/web/v1/customers/{customer_id}", status_code=302)