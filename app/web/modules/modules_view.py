# app/web/modules_view.py or your preferred location
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.utils import auth
from app.models.module import Module
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/settings/modules/misp")
def misp_module_config(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    misp_entry = db.query(Module).filter(Module.name == "MISP", Module.is_local == False).first()
    verify_cert_entry = db.query(Module).filter(Module.name == "MISP_VERIFY_CERT", Module.is_local == True).first()

    is_configured = misp_entry is not None and misp_entry.remote_url and misp_entry.remote_api_key

    context = {
        "request": request,
        "user": user,
        "misp_entry": misp_entry,
        "verify_cert_entry": verify_cert_entry,
        "is_configured": is_configured
    }

    return templates.TemplateResponse("modules/misp_module.html", context)

@router.get("/settings/modules/maxmind")
def maxmind_module_config(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    user_id_entry = db.query(Module).filter(Module.name == "MaxMind-GeoIP-UserID", Module.is_local == True).first()
    license_key_entry = db.query(Module).filter(Module.name == "MaxMind-GeoIP-Key", Module.is_local == True).first()

    is_configured = user_id_entry is not None and license_key_entry is not None

    success = request.query_params.get("success")
    error = request.query_params.get("error")

    context = {
        "request": request,
        "user": user,
        "user_id_entry": user_id_entry,
        "license_key_entry": license_key_entry,
        "is_configured": is_configured,
        "success": success,
        "error": error
    }

    return templates.TemplateResponse("modules/maxmind_module.html", context)


@router.get("/settings/modules/virustotal")
def virustotal_module_config(
    request: Request,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    vt_entry = db.query(Module).filter(Module.name == "VirusTotal", Module.is_local == False).first()
    is_configured = vt_entry is not None and vt_entry.remote_url and vt_entry.remote_api_key

    context = {
        "request": request,
        "user": user,
        "vt_entry": vt_entry,
        "is_configured": is_configured
    }

    return templates.TemplateResponse("modules/virustotal_module.html", context)


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
    name = name.strip()

    existing_module = (
        db.query(Module)
        .filter(Module.name == name, Module.is_local == is_local)
        .first()
    )

    if existing_module:
        # Update existing
        existing_module.local_key = local_key.strip() if local_key else None
        existing_module.remote_url = remote_url.strip() if remote_url else None
        existing_module.remote_api_key = remote_api_key.strip() if remote_api_key else None
    else:
        # Create new
        new_module = Module(
            name=name,
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


