"""Mật khẩu PBKDF2-SHA256 và access-token JWT cho tính năng ứng tuyển."""
import base64
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.user import User

_ITERATIONS = 600_000
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    raw = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, _ITERATIONS)
    return f'pbkdf2_sha256${_ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(raw).decode()}'


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored.split('$')
        if algorithm != 'pbkdf2_sha256' or not 100_000 <= int(iterations) <= 2_000_000:
            return False
        derived = hashlib.pbkdf2_hmac('sha256', password.encode(), base64.b64decode(salt), int(iterations))
        return hmac.compare_digest(derived, base64.b64decode(digest))
    except (ValueError, TypeError):
        return False


def _signing_key() -> str:
    secret = os.getenv('JWT_SECRET_KEY', '')
    if len(secret) < 32 or secret.startswith('CHANGE_ME'):
        raise HTTPException(status_code=503, detail='Chưa cấu hình JWT_SECRET_KEY an toàn trong backend/.env')
    return secret


def create_access_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {'sub': str(user.user_id), 'iat': now, 'exp': now + timedelta(hours=2), 'iss': 'unicareer'},
        _signing_key(), algorithm='HS256'
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not credentials or credentials.scheme.lower() != 'bearer':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Cần đăng nhập để tiếp tục', headers={'WWW-Authenticate': 'Bearer'})
    try:
        claims = jwt.decode(credentials.credentials, _signing_key(), algorithms=['HS256'], issuer='unicareer', options={'require': ['sub', 'exp', 'iat', 'iss']})
        sub = claims['sub']
        if not isinstance(sub, str) or not sub.isdecimal() or int(sub) <= 0:
            raise ValueError('invalid subject')
    except (InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail='Phiên đăng nhập đã hết hạn hoặc không hợp lệ', headers={'WWW-Authenticate': 'Bearer'})
    user = db.get(User, int(sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail='Tài khoản không tồn tại hoặc đã bị khóa')
    return user


def require_candidate(user: User = Depends(get_current_user)) -> User:
    if user.role != 'CANDIDATE':
        raise HTTPException(status_code=403, detail='Chỉ tài khoản ứng viên mới được sử dụng chức năng này')
    return user
