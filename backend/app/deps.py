from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .db import get_db
from .models import User
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = decode_token(token)
    user = db.get(User, payload['user_id'])
    if user is None or user.email != payload['sub'] or user.role != payload['role']:
        raise HTTPException(status_code=401, detail='Không xác thực được tài khoản')
    if not user.is_active:
        raise HTTPException(status_code=403, detail='Tài khoản đã bị khóa')
    return user

def require_role(*roles):
    def dependency(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail='Không có quyền thực hiện thao tác này')
        return user
    return dependency
