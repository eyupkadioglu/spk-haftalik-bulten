from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user
from typing import List

router = APIRouter()


@router.get("/", response_model=List[schemas.ArchiveOut])
def list_archives(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Archive).order_by(
        models.Archive.year.desc(), models.Archive.week_number.desc()
    ).all()


@router.get("/{archive_id}", response_model=schemas.ArchiveOut)
def get_archive(archive_id: str, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    a = db.query(models.Archive).filter(models.Archive.id == archive_id).first()
    if not a:
        raise HTTPException(404, "Arşiv bulunamadı")
    return a
