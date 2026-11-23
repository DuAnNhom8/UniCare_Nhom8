"""
Pydantic Schemas cho xác thực và quản lý tài khoản (Authentication)
Theo đặc tả SRS UniCareer mục 10.2.1 & 11.2 (Authentication Module)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserRegister(BaseModel):
    email: str = Field(..., min_length=5, max_length=100, description="Email đăng nhập duy nhất")
    password: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")
    role: str = Field("CANDIDATE", description="Vai trò: CANDIDATE, EMPLOYER, ADMIN")
    full_name: Optional[str] = Field(None, description="Họ tên sinh viên (nếu là CANDIDATE)")
    company_name: Optional[str] = Field(None, description="Tên công ty (nếu là EMPLOYER)")


class UserLogin(BaseModel):
    email: str = Field(..., min_length=5, max_length=100, description="Email đăng nhập")
    password: str = Field(..., description="Mật khẩu")


class UserResponse(BaseModel):
    user_id: int
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    detail: Optional[str] = None
