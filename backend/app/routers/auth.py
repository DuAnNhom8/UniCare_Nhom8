from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import bearer_scheme, get_current_user, revoke_access_token
from app.models.user import UserModel
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import login_user, register_user


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    return register_user(db, request)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return login_user(db, request)


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu thông tin đăng nhập",
        )
    revoke_access_token(db, current_user, credentials.credentials)
    return {"message": "Đăng xuất thành công"}


@router.get("/me")
def get_me(current_user: UserModel = Depends(get_current_user)):
    roles = sorted({role.name.lower() for role in current_user.roles}.union({current_user.role.lower()}))
    full_name = current_user.profile.full_name if current_user.profile is not None else None
    return {
        "id": current_user.id,
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": full_name,
        "role": current_user.role.lower(),
        "is_active": current_user.is_active,
        "roles": roles,
    }