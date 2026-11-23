from datetime import datetime, timedelta, timezone
import jwt
from fastapi import HTTPException, status
from .config import JWT_EXPIRES_MINUTES, JWT_SECRET


def hash_password(password: str) -> str:
    import bcrypt
    if len(password.encode('utf-8')) > 72:
        raise ValueError('Mật khẩu vượt quá 72 bytes theo giới hạn bcrypt')
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    import bcrypt
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, UnicodeError):
        return False


def access_token(user) -> str:
    if len(JWT_SECRET) < 32 or JWT_SECRET == 'replace-with-a-random-64-character-secret':
        raise RuntimeError('Cần cấu hình JWT_SECRET ngẫu nhiên dài ít nhất 32 ký tự trong .env')
    payload = {
        'sub': user.email,
        'user_id': user.user_id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRES_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def decode_token(token: str) -> dict:
    if len(JWT_SECRET) < 32:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='JWT_SECRET chưa được cấu hình')
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'], options={'require': ['exp', 'sub', 'user_id', 'role']})
        if not isinstance(payload.get('user_id'), int):
            raise jwt.InvalidTokenError('invalid user_id')
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Phiên đăng nhập đã hết hạn', headers={'WWW-Authenticate': 'Bearer'})
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Token không hợp lệ', headers={'WWW-Authenticate': 'Bearer'})
