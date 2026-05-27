from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user
from typing import List

router = APIRouter()


def _log(db, action, user, bulletin_id=None, section_id=None, summary=None):
    db.add(models.Log(
        action=action,
        user_id=user.id,
        user_name=user.name,
        user_role=user.role_code,
        bulletin_id=bulletin_id,
        section_id=section_id,
        new_value_summary=summary,
    ))
    db.commit()


@router.get("/", response_model=List[schemas.BulletinOut])
def list_bulletins(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Bulletin).order_by(
        models.Bulletin.year.desc(), models.Bulletin.week_number.desc()
    ).all()


@router.post("/", response_model=schemas.BulletinOut)
def create_bulletin(
    b: schemas.BulletinCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    bulletin = models.Bulletin(**b.model_dump(), created_by=current_user.id)
    db.add(bulletin)
    db.commit()
    db.refresh(bulletin)
    _log(db, "BULLETIN_CREATED", current_user, bulletin_id=bulletin.id, summary=bulletin.title)
    return bulletin


@router.get("/{bulletin_id}", response_model=schemas.BulletinOut)
def get_bulletin(bulletin_id: str, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    b = db.query(models.Bulletin).filter(models.Bulletin.id == bulletin_id).first()
    if not b:
        raise HTTPException(404, "Bülten bulunamadı")
    return b


@router.put("/{bulletin_id}", response_model=schemas.BulletinOut)
def update_bulletin(
    bulletin_id: str,
    b_in: schemas.BulletinUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    b = db.query(models.Bulletin).filter(models.Bulletin.id == bulletin_id).first()
    if not b:
        raise HTTPException(404, "Bülten bulunamadı")
    for k, v in b_in.model_dump(exclude_unset=True).items():
        setattr(b, k, v)
    db.commit()
    db.refresh(b)
    _log(db, "BULLETIN_UPDATED", current_user, bulletin_id=bulletin_id)
    return b


@router.delete("/{bulletin_id}")
def delete_bulletin(
    bulletin_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    b = db.query(models.Bulletin).filter(models.Bulletin.id == bulletin_id).first()
    if not b:
        raise HTTPException(404, "Bülten bulunamadı")
    db.delete(b)
    db.commit()
    return {"ok": True}


@router.get("/{bulletin_id}/sections", response_model=List[schemas.SectionOut])
def get_bulletin_sections(
    bulletin_id: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    return db.query(models.Section).filter(models.Section.bulletin_id == bulletin_id).all()
