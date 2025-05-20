from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.assets import Asset
from app.schemas.assets import AssetCreate, AssetUpdate
from app.utils import auth

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/assets", response_class=HTMLResponse)
def list_assets(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    assets = db.query(Asset).order_by(Asset.created_at.desc()).all()
    return templates.TemplateResponse("assets/assets_list.html", {"request": request, "assets": assets})


@router.get("/assets/new", response_class=HTMLResponse)
def new_asset_form(request: Request, user=Depends(auth.get_current_user)):
    return templates.TemplateResponse("assets/assets_form.html", {"request": request, "asset": None})


@router.post("/assets/new")
def create_asset(
    request: Request,
    name: str = Form(...),
    ip_address: Optional[str] = Form(None),
    hostname: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    new_asset = Asset(
        name=name.strip(),
        ip_address=ip_address,
        hostname=hostname,
        type=type,
        owner=owner,
        tags=tags,
        notes=notes,
    )
    db.add(new_asset)
    db.commit()
    return RedirectResponse(url="/web/v1/assets", status_code=303)

def serialize_asset(asset):
    return {
        "id": asset.id,
        "name": asset.name,
        "ip_address": asset.ip_address,
        "hostname": asset.hostname,
        "type": asset.type,
        "owner": asset.owner,
        "tags": asset.tags,
        "notes": asset.notes
    }

@router.get("/assets/{asset_id}", response_class=HTMLResponse)
def asset_detail_view(
    request: Request,
    asset_id: int,
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    return templates.TemplateResponse("assets/assets_detail.html", {
        "request": request,
        "asset": asset,
        "asset_json": serialize_asset(asset)
    })

@router.get("/assets/{asset_id}/edit", response_class=HTMLResponse)
def edit_asset_form(asset_id: int, request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return templates.TemplateResponse("assets/assets_form.html", {"request": request, "asset": asset})


@router.post("/assets/{asset_id}/edit")
def update_asset(
    asset_id: int,
    name: str = Form(...),
    ip_address: Optional[str] = Form(None),
    hostname: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.name = name.strip()
    asset.ip_address = ip_address
    asset.hostname = hostname
    asset.type = type
    asset.owner = owner
    asset.tags = tags
    asset.notes = notes

    db.commit()
    return RedirectResponse(url=f"/web/v1/assets", status_code=303)


@router.post("/assets/{asset_id}/delete")
def delete_asset(asset_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()
    return RedirectResponse(url="/web/v1/assets", status_code=303)

@router.post("/assets/edit")
def update_asset_modal(
    asset_id: int = Form(...),
    name: str = Form(...),
    ip_address: Optional[str] = Form(None),
    hostname: Optional[str] = Form(None),
    type: Optional[str] = Form(None),
    owner: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.name = name.strip()
    asset.ip_address = ip_address
    asset.hostname = hostname
    asset.type = type
    asset.owner = owner
    asset.tags = tags
    asset.notes = notes

    db.commit()
    return RedirectResponse(url=f"/web/v1/assets/{asset_id}", status_code=303)