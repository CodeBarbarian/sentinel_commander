from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.models.customer import Customer
from app.core.database import get_db
from app.utils import auth
from fastapi.templating import Jinja2Templates

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
