from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import markdown
from app.core.database import get_db
from app.models.playbooks import Playbook
from app.schemas.playbooks import PlaybookOut
from app.utils import auth
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/playbooks", response_class=HTMLResponse)
def list_playbooks(request: Request, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    playbooks = db.query(Playbook).order_by(Playbook.name.asc()).all()

    rendered = []
    for pb in playbooks:
        rendered_steps = markdown.markdown(pb.steps or "", extensions=["fenced_code", "tables"])
        rendered.append({
            **PlaybookOut.model_validate(pb).dict(),
            "rendered_steps": rendered_steps
        })

    return templates.TemplateResponse("playbooks/playbooks.html", {
        "request": request,
        "playbooks": rendered
    })

@router.post("/playbooks")
def create_playbook(
    name: str = Form(...),
    description: str = Form(""),
    steps: str = Form(""),
    classification: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    playbook = Playbook(
        name=name.strip(),
        description=description.strip(),
        steps=steps.strip(),
        classification=classification.strip(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(playbook)
    db.commit()

    return RedirectResponse(url="/web/v1/playbooks", status_code=303)

@router.post("/playbooks/{playbook_id}/edit")
def edit_playbook(
    playbook_id: int,
    name: str = Form(...),
    description: str = Form(""),
    steps: str = Form(""),
    classification: str = Form(""),
    db: Session = Depends(get_db),
    user=Depends(auth.get_current_user)
):
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    playbook.name = name.strip()
    playbook.description = description.strip()
    playbook.steps = steps.strip()
    playbook.classification = classification.strip()
    playbook.updated_at = datetime.utcnow()
    db.commit()

    return RedirectResponse(url="/web/v1/playbooks", status_code=303)

@router.post("/playbooks/{playbook_id}/delete")
def delete_playbook(playbook_id: int, db: Session = Depends(get_db), user=Depends(auth.get_current_user)):
    playbook = db.query(Playbook).filter(Playbook.id == playbook_id).first()
    if not playbook:
        raise HTTPException(status_code=404, detail="Playbook not found")

    db.delete(playbook)
    db.commit()

    return RedirectResponse(url="/web/v1/playbooks", status_code=303)
