"""
Dịch vụ xác thực và quản lý tài khoản (Authentication Service)
Theo đặc tả SRS UniCareer mục 11.2 (Authentication Module)
"""

import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.models.user import User
from backend.app.models.candidate import Candidate
from backend.app.models.company import Company
from backend.app.schemas.auth import UserRegister


def hash_password(password: str) -> str:
    """Băm mật khẩu sử dụng SHA-256 an toàn và chuẩn hóa"""
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """Kiểm tra mật khẩu khớp với mã băm hoặc tài khoản seed demo"""
    if not stored_hash or not plain_password:
        return False
    # Kiểm tra khớp SHA-256
    if hash_password(plain_password) == stored_hash:
        return True
    # Hỗ trợ tài khoản mẫu ban đầu (như 'demo123')
    if plain_password == stored_hash:
        return True
    return False


def register_user(db: Session, data: UserRegister) -> User:
    """
    Đăng ký tài khoản người dùng mới:
    - Kiểm tra email không được trùng lặp
    - Tạo tài khoản trong bảng USERS
    - Tự động liên kết tạo CANDIDATE hoặc COMPANY tương ứng với vai trò
    """
    normalized_email = data.email.strip().lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{normalized_email}' đã được đăng ký trong hệ thống."
        )

    # Chuẩn hóa vai trò
    role = data.role.strip().upper()
    if role not in ["CANDIDATE", "EMPLOYER", "ADMIN"]:
        role = "CANDIDATE"

    # Tạo User mới
    new_user = User(
        email=normalized_email,
        password_hash=hash_password(data.password),
        role=role,
        is_active=True
    )
    db.add(new_user)
    db.flush()  # Lấy new_user.user_id

    # Khởi tạo hồ sơ phụ thuộc vai trò
    if role == "CANDIDATE":
        candidate_name = data.full_name.strip() if data.full_name else normalized_email.split("@")[0].title()
        candidate = Candidate(
            candidate_id=new_user.user_id,
            full_name=candidate_name,
            university="Chưa cập nhật",
            major="Chưa cập nhật"
        )
        db.add(candidate)
    elif role == "EMPLOYER":
        company_title = data.company_name.strip() if data.company_name else f"Công ty của {normalized_email.split('@')[0]}"
        company = Company(
            employer_id=new_user.user_id,
            company_name=company_title,
            industry="Công nghệ thông tin",
            location="TP. Hồ Chí Minh"
        )
        db.add(company)

    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Xác thực đăng nhập người dùng:
    - Kiểm tra email tồn tại
    - Kiểm tra tài khoản không bị vô hiệu hóa
    - So khớp mật khẩu
    """
    normalized_email = email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản của bạn đã bị khóa bởi Quản trị viên. Vui lòng liên hệ ban quản trị."
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản hoặc mật khẩu không chính xác."
        )

    return user
