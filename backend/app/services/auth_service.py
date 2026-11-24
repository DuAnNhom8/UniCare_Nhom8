from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.role import RoleModel
from app.models.user import UserModel
from app.models.profile import ProfileModel
from app.schemas.auth import LoginRequest, RegisterRequest


ALLOWED_PUBLIC_ROLES = {"candidate", "employer"}


def seed_roles(db: Session) -> None:
    for name in ("candidate", "employer", "admin"):
        role = db.query(RoleModel).filter(RoleModel.name == name).first()
        if role is None:
            db.add(RoleModel(name=name))
    db.commit()


def register_user(db: Session, request: RegisterRequest) -> dict:
    role_name = request.role.strip().lower()
    if role_name not in ALLOWED_PUBLIC_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vai trò đăng ký chỉ có thể là candidate hoặc employer",
        )

    existing = db.query(UserModel).filter(UserModel.email == str(request.email).lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã được sử dụng",
        )

    role = db.query(RoleModel).filter(RoleModel.name == role_name).first()
    if role is None:
        seed_roles(db)
        role = db.query(RoleModel).filter(RoleModel.name == role_name).first()

    user = UserModel(
        email=str(request.email).lower(),
        hashed_password=hash_password(request.password),
        role=role_name,
    )
    user.roles.append(role)
    full_name = request.full_name.strip()
    if full_name:
        user.profile = ProfileModel(full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return build_login_result(db, user)


def login_user(db: Session, request: LoginRequest) -> dict:
    user = db.query(UserModel).filter(UserModel.email == str(request.email).lower()).first()
    if user is None or not user.is_active or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng",
        )
    return build_login_result(db, user)


def build_login_result(db: Session, user: UserModel) -> dict:
    role_names = {role.name for role in user.roles}
    role_names.add(user.role)
    full_name = user.profile.full_name if user.profile is not None else None
    return {
        "access_token": create_access_token(user.id),
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "user_id": user.id,
            "email": user.email,
            "full_name": full_name,
            "role": user.role.lower(),
            "roles": sorted(role_names),
        },
    }