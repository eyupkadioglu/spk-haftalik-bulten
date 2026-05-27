from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user
from typing import List

router = APIRouter()


def _log(db, action, user, bulletin_id=None, section_id=None, entry_id=None, old_value=None):
    db.add(models.Log(
        action=action,
        user_id=user.id, user_name=user.name, user_role=user.role_code,
        bulletin_id=bulletin_id, section_id=section_id, entry_id=entry_id,
        old_value=old_value,
    ))
    db.commit()


def _bulletin_id(db, section_id):
    s = db.query(models.Section).filter(models.Section.id == section_id).first()
    return s.bulletin_id if s else None


@router.get("/section/{section_id}", response_model=List[schemas.EntryOut])
def list_entries(
    section_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return db.query(models.Entry).filter(
        models.Entry.section_id == section_id
    ).order_by(models.Entry.order).all()


@router.post("/section/{section_id}", response_model=schemas.EntryOut)
def create_entry(
    section_id: str,
    e_in: schemas.EntryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not db.query(models.Section).filter(models.Section.id == section_id).first():
        raise HTTPException(404, "Bölüm bulunamadı")
    entry = models.Entry(
        **e_in.model_dump(),
        section_id=section_id,
        created_by=current_user.id,
        created_by_role=current_user.role_code,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    _log(db, "ENTRY_CREATED", current_user,
         bulletin_id=_bulletin_id(db, section_id), section_id=section_id, entry_id=entry.id)
    return entry


@router.get("/{entry_id}", response_model=schemas.EntryOut)
def get_entry(entry_id: str, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Kayıt bulunamadı")
    return entry


@router.put("/{entry_id}", response_model=schemas.EntryOut)
def update_entry(
    entry_id: str,
    e_in: schemas.EntryUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Kayıt bulunamadı")
    old_content = entry.content_html
    for k, v in e_in.model_dump(exclude_unset=True).items():
        setattr(entry, k, v)
    db.commit()
    db.refresh(entry)
    _log(db, "SECTION_UPDATED", current_user,
         bulletin_id=_bulletin_id(db, entry.section_id),
         section_id=entry.section_id, entry_id=entry_id, old_value=old_content)
    return entry


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Kayıt bulunamadı")
    sid = entry.section_id
    db.delete(entry)
    db.commit()
    _log(db, "ENTRY_DELETED", current_user,
         bulletin_id=_bulletin_id(db, sid), section_id=sid, entry_id=entry_id)
    return {"ok": True}


@router.post("/{entry_id}/approve")
def approve_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Bulunamadı")
    entry.approval_status = "APPROVED"
    db.commit()
    _log(db, "ENTRY_APPROVED", current_user,
         bulletin_id=_bulletin_id(db, entry.section_id), section_id=entry.section_id, entry_id=entry_id)
    return {"approval_status": entry.approval_status}


@router.post("/{entry_id}/return")
def return_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    entry = db.query(models.Entry).filter(models.Entry.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Bulunamadı")
    entry.approval_status = "RETURNED"
    db.commit()
    _log(db, "ENTRY_RETURNED", current_user,
         bulletin_id=_bulletin_id(db, entry.section_id), section_id=entry.section_id, entry_id=entry_id)
    return {"approval_status": entry.approval_status}
