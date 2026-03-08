from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    phone_exists = db.scalar(select(User).where(User.phone == payload.phone))
    if phone_exists:
        raise HTTPException(status_code=400, detail="Phone number already registered")

    email_exists = db.scalar(select(User).where(User.email == payload.email))
    if email_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        phone=payload.phone,
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        is_admin=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    phone_input = payload.phone.strip()
    lookup_phone = settings.admin_phone if phone_input.lower() == "admin" else phone_input
    user = db.scalar(select(User).where(User.phone == lookup_phone))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect phone or password")
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user
