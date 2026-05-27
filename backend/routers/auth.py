from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import verify_password, create_token, hash_password, get_current_user

router = APIRouter()


@router.post("/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == req.username,
        models.User.is_active == True,
    ).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Kullanıcı adı veya şifre hatalı")
    return {
        "access_token": create_token(user.id),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "username": user.username,
            "role_code": user.role_code,
            "department_id": user.department_id,
        },
    }


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/setup", response_model=schemas.UserOut)
def initial_setup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """İlk admin hesabını oluşturur. Yalnızca veritabanı boşken çalışır."""
    if db.query(models.User).count() > 0:
        raise HTTPException(status_code=400, detail="Kurulum zaten tamamlandı")
    user = models.User(
        name=user_in.name,
        username=user_in.username,
        password_hash=hash_password(user_in.password),
        role_code="ADMIN",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
