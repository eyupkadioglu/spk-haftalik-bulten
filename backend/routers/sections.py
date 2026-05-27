from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
import models, schemas
from auth import get_current_user
from typing import List, Optional

router = APIRouter()

# status → {approve: next, return: prev}
TRANSITIONS = {
    "SECTION_PREP":   {"submit": "DB_APPROVAL"},
    "DB_APPROVAL":    {"approve": "KBY_APPROVAL",  "return": "SECTION_PREP"},
    "KBY_APPROVAL":   {"approve": "KBY_APPROVED",  "return": "DB_APPROVAL"},
    "KBY_APPROVED":   {"approve": "KOB_READY",     "return": "KBY_APPROVAL"},
    "CHAIR_APPROVAL": {"approve": "PUBLISHED",     "return": "KBY_APPROVED"},
}

ACTION_LOG = {
    "submit":  "SECTION_SUBMITTED",
    "approve": "SECTION_APPROVED",
    "return":  "SECTION_RETURNED",
}


class ActionRequest(BaseModel):
    reason: Optional[str] = None


def _log(db, action, user, bulletin_id=None, section_id=None, reason=None):
    db.add(models.Log(
        action=action,
        user_id=user.id, user_name=user.name, user_role=user.role_code,
        bulletin_id=bulletin_id, section_id=section_id, reason=reason,
    ))
    db.commit()


@router.get("/{section_id}", response_model=schemas.SectionOut)
def get_section(section_id: str, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    s = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not s:
        raise HTTPException(404, "Bölüm bulunamadı")
    return s


@router.post("/", response_model=schemas.SectionOut)
def create_section(
    s_in: schemas.SectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    s = models.Section(**s_in.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    _log(db, "SECTION_CREATED", current_user, bulletin_id=s.bulletin_id, section_id=s.id)
    return s


@router.put("/{section_id}", response_model=schemas.SectionOut)
def update_section(
    section_id: str,
    s_in: schemas.SectionUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    s = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not s:
        raise HTTPException(404, "Bölüm bulunamadı")
    for k, v in s_in.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    _log(db, "SECTION_UPDATED", current_user, bulletin_id=s.bulletin_id, section_id=s.id)
    return s


@router.delete("/{section_id}")
def delete_section(
    section_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    s = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not s:
        raise HTTPException(404, "Bölüm bulunamadı")
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.post("/{section_id}/action/{action}")
def section_action(
    section_id: str,
    action: str,
    req: ActionRequest = ActionRequest(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    s = db.query(models.Section).filter(models.Section.id == section_id).first()
    if not s:
        raise HTTPException(404, "Bölüm bulunamadı")
    transitions = TRANSITIONS.get(s.status, {})
    new_status = transitions.get(action)
    if not new_status:
        raise HTTPException(400, f"'{s.status}' durumunda '{action}' işlemi yapılamaz")
    s.status = new_status
    db.commit()
    _log(db, ACTION_LOG.get(action, action.upper()), current_user,
         bulletin_id=s.bulletin_id, section_id=s.id, reason=req.reason)
    return {"status": s.status}
