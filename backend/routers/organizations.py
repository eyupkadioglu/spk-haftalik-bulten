from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import get_current_user, hash_password
from typing import List

router = APIRouter()


def _require_admin(user: models.User):
    if user.role_code != "ADMIN":
        raise HTTPException(403, "Yetki yok")


# ── Departments ───────────────────────────────────────────────────────────────

@router.get("/departments", response_model=List[schemas.DepartmentOut])
def list_departments(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.Department).order_by(models.Department.name).all()


@router.post("/departments", response_model=schemas.DepartmentOut)
def create_department(
    dept: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_admin(current_user)
    d = models.Department(**dept.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.put("/departments/{dept_id}", response_model=schemas.DepartmentOut)
def update_department(
    dept_id: str,
    dept: schemas.DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_admin(current_user)
    d = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not d:
        raise HTTPException(404, "Daire bulunamadı")
    for k, v in dept.model_dump(exclude_unset=True).items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/departments/{dept_id}")
def delete_department(
    dept_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_admin(current_user)
    d = db.query(models.Department).filter(models.Department.id == dept_id).first()
    if not d:
        raise HTTPException(404, "Daire bulunamadı")
    db.delete(d)
    db.commit()
    return {"ok": True}


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    return db.query(models.User).order_by(models.User.name).all()


@router.post("/users", response_model=schemas.UserOut)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_admin(current_user)
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(400, "Bu kullanıcı adı zaten mevcut")
    user = models.User(
        name=user_in.name,
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        role_code=user_in.role_code,
        department_id=user_in.department_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=schemas.UserOut)
def update_user(
    user_id: str,
    user_in: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_admin(current_user)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    data = user_in.model_dump(exclude_unset=True)
    if "password" in data:
        user.password_hash = hash_password(data.pop("password"))
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _require_admin(current_user)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(404, "Kullanıcı bulunamadı")
    db.delete(user)
    db.commit()
    return {"ok": True}
