# app/web/modules_view.py or your preferred location
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils import auth
from app.models.module import Module

router = APIRouter()


@router.post("/modules/create")
def create_module(
    name: str = Form(...),
    is_local: bool = Form(...),
    local_key: str = Form(None),
    remote_url: str = Form(None),
    remote_api_key: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    new_module = Module(
        name=name.strip(),
        is_local=is_local,
        local_key=local_key.strip() if local_key else None,
        remote_url=remote_url.strip() if remote_url else None,
        remote_api_key=remote_api_key.strip() if remote_api_key else None
    )
    db.add(new_module)
    db.commit()
    return RedirectResponse("/web/v1/settings/modules", status_code=302)


@router.post("/modules/update")
def update_module(
    id: int = Form(...),
    name: str = Form(...),
    is_local: bool = Form(...),
    local_key: str = Form(None),
    remote_url: str = Form(None),
    remote_api_key: str = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    module = db.query(Module).filter(Module.id == id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    module.name = name.strip()
    module.is_local = is_local
    module.local_key = local_key.strip() if local_key else None
    module.remote_url = remote_url.strip() if remote_url else None
    module.remote_api_key = remote_api_key.strip() if remote_api_key else None

    db.commit()
    return RedirectResponse("/web/v1/settings/modules", status_code=302)


@router.post("/modules/delete")
def delete_module(id: int = Form(...), db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    module = db.query(Module).filter(Module.id == id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")
    db.delete(module)
    db.commit()
    return RedirectResponse("/web/v1/settings/modules", status_code=302)
