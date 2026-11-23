"""Đăng ký và đăng nhập thật, trả JWT dùng cho API ứng tuyển."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import create_access_token, get_current_user, hash_password, verify_password
from backend.app.models.user import User
from backend.app.schemas.auth import CurrentUser, LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix='/auth', tags=['Xác thực'])


@router.post('/register', response_model=CurrentUser, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail='Email đã được đăng ký')
    user = User(email=data.email, password_hash=hash_password(data.password), role=data.role)
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail='Email đã được đăng ký')
    return user


@router.post('/login', response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Email hoặc mật khẩu không chính xác')
    return TokenResponse(access_token=create_access_token(user))


@router.get('/me', response_model=CurrentUser)
def who_am_i(user: User = Depends(get_current_user)):
    return user
