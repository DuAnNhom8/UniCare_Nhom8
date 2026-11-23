"""
API Router cho phân hệ Xác thực và Tài khoản (Auth Router)
Theo đặc tả SRS UniCareer mục 10.2.1 & 11.2 (Authentication Module)
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.auth import UserRegister, UserLogin, UserResponse, LoginResponse
from backend.app.services import auth_service
from backend.app.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Xác thực & Tài khoản (Authentication)"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới"
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Đăng ký tài khoản mới trong hệ thống UniCareer:
    - **email**: Email hợp lệ, duy nhất
    - **password**: Tối thiểu 6 ký tự
    - **role**: CANDIDATE (Sinh viên), EMPLOYER (Nhà tuyển dụng), ADMIN
    - Tự động tạo hồ sơ mặc định tương ứng với vai trò
    """
    user = auth_service.register_user(db, data)
    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Đăng nhập hệ thống"
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Xác thực thông tin đăng nhập và trả về thông tin người dùng cùng phiên truy cập
    """
    user = auth_service.authenticate_user(db, data.email, data.password)
    # Token định danh phiên đơn giản cho hệ thống web REST
    token_str = f"unicareer_token_{user.user_id}_{user.role.lower()}"
    return LoginResponse(
        access_token=token_str,
        token_type="bearer",
        user=UserResponse.model_validate(user),
        detail=f"Đăng nhập thành công với vai trò {user.role}"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Lấy thông tin tài khoản đang đăng nhập"
)
def get_current_user(
    user_id: int = Query(..., description="ID người dùng"),
    db: Session = Depends(get_db)
):
    """Lấy thông tin người dùng qua user_id"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại."
        )
    return user
