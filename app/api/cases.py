from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from fastapi.templating import Jinja2Templates

from app.core.database import get_db
from app.models.case import Case
from app.models.case_tag import CaseTag
from app.schemas.case import CaseCreate, CaseUpdate, CaseResponse
from app.schemas.case_tag import CaseTagCreate, CaseTagOut

from app.core.security import require_admin_api_key
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/cases", response_model=List[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    cases = db.query(Case).order_by(Case.created_at.desc()).all()
    return [CaseResponse.model_validate(c) for c in cases]


@router.post("/cases", response_model=CaseResponse)
def create_case(payload: CaseCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    tags = data.pop("tags", [])

    new_case = Case(**data)
    new_case.tags = [CaseTag(tag=tag) for tag in tags]

    db.add(new_case)
    db.commit()
    db.refresh(new_case)
    return CaseResponse.model_validate(new_case)


@router.patch("/cases/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, payload: CaseUpdate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    updates = payload.model_dump(exclude_unset=True)
    new_tags = updates.pop("tags", None)

    for field, value in updates.items():
        setattr(case, field, value)

    if new_tags is not None:
        # Clear existing tags
        case.tags.clear()
        db.flush()
        # Add updated tags
        case.tags = [CaseTag(tag=tag) for tag in new_tags]

    db.commit()
    db.refresh(case)
    return CaseResponse.model_validate(case)


@router.delete("/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    db.delete(case)
    db.commit()
    return {"detail": f"Case {case_id} deleted successfully"}


@router.get("/cases/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return CaseResponse.model_validate(case)


@router.post("/cases/{case_id}/tags", response_model=CaseTagOut)
def add_case_tag(case_id: int, payload: CaseTagCreate, db: Session = Depends(get_db)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    tag = CaseTag(case_id=case_id, tag=payload.tag)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag
