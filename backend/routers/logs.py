from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user
from typing import List, Optional

router = APIRouter()


@router.get("/", response_model=List[schemas.LogOut])
def list_logs(
    bulletin_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
):
    q = db.query(models.Log)
    if bulletin_id:
        q = q.filter(models.Log.bulletin_id == bulletin_id)
    if action:
        q = q.filter(models.Log.action == action)
    return q.order_by(models.Log.timestamp.desc()).limit(limit).all()
