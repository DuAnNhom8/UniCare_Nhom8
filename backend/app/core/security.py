import base64
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY
from app.core.database import get_db
from app.models.ai import RevokedTokenModel
from app.models.user import UserModel


bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    password_digest = hashlib.sha256(password.encode("utf-8")).digest()
    return bcrypt.hashpw(password_digest, bcrypt.gensalt()).decode("ascii")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        password_digest = hashlib.sha256(plain_password.encode("utf-8")).digest()
        return bcrypt.checkpw(password_digest, hashed_password.encode("ascii"))
    except (TypeError, ValueError):
        return False


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": int(time.time()) + ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_part = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode("ascii")
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_part.encode("ascii"),
        hashlib.sha256,
    ).digest()
    signature_part = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{payload_part}.{signature_part}"


def decode_access_token(token: str) -> int:
    try:
        payload_part, signature_part = token.split(".", 1)
        expected = hmac.new(
            SECRET_KEY.encode("utf-8"),
            payload_part.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual = base64.urlsafe_b64decode(signature_part + "=" * (-len(signature_part) % 4))
        if not hmac.compare_digest(expected, actual):
            raise ValueError("invalid signature")

        payload_bytes = base64.urlsafe_b64decode(payload_part + "=" * (-len(payload_part) % 4))
        payload = json.loads(payload_bytes)
        if payload["exp"] < int(time.time()):
            raise ValueError("token expired")
        return int(payload["sub"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn",
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> UserModel:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Yêu cầu thông tin đăng nhập",
        )

    user_id = decode_access_token(credentials.credentials)
    token_digest = hashlib.sha256(credentials.credentials.encode("utf-8")).hexdigest()
    revoked = (
        db.query(RevokedTokenModel.id)
        .filter(
            RevokedTokenModel.token_digest == token_digest,
            RevokedTokenModel.expires_at > datetime.now(timezone.utc).replace(tzinfo=None),
        )
        .first()
    )
    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Phiên đăng nhập đã kết thúc",
        )
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản không tồn tại hoặc đã bị khóa",
        )
    return user


def revoke_access_token(db: Session, user: UserModel, token: str) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db.query(RevokedTokenModel).filter(RevokedTokenModel.expires_at <= now).delete(
        synchronize_session=False,
    )
    db.add(
        RevokedTokenModel(
            user_id=user.id,
            token_digest=hashlib.sha256(token.encode("utf-8")).hexdigest(),
            expires_at=now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
    )
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Không thể kết thúc phiên đăng nhập",
        ) from error


def require_roles(*allowed_roles: str):
    normalized_roles = {role.lower() for role in allowed_roles}

    def role_dependency(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        assigned_roles = {role.name.lower() for role in current_user.roles}
        assigned_roles.add(current_user.role.lower())
        if not assigned_roles.intersection(normalized_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền truy cập",
            )
        return current_user

    return role_dependency