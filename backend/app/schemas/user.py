"""
Pydantic Schemas cho hồ sơ ứng viên (Candidate) và quản trị người dùng (Admin User Management)
Theo đặc tả SRS UniCareer mục 10.2.2 & 11.2 (Candidate & Admin Modules)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Schema cập nhật hồ sơ ứng viên (CANDIDATE)
class CandidateProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Họ và tên sinh viên")
    phone: Optional[str] = Field(None, max_length=20, description="Số điện thoại")
    university: Optional[str] = Field(None, max_length=150, description="Trường đại học")
    major: Optional[str] = Field(None, max_length=100, description="Chuyên ngành")
    skills: Optional[str] = Field(None, description="Kỹ năng chính (JSON hoặc chuỗi)")
    bio: Optional[str] = Field(None, description="Giới thiệu bản thân")
    cv_url: Optional[str] = Field(None, max_length=255, description="Đường dẫn file CV")


# Schema thông tin hồ sơ ứng viên trả về
class CandidateProfileResponse(BaseModel):
    candidate_id: int
    full_name: str
    phone: Optional[str] = None
    university: Optional[str] = None
    major: Optional[str] = None
    skills: Optional[str] = None
    bio: Optional[str] = None
    cv_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    email: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


# Schema cập nhật trạng thái tài khoản bởi Admin (khóa/mở)
class UserStatusUpdate(BaseModel):
    is_active: bool = Field(..., description="Trạng thái tài khoản (True: Hoạt động, False: Khóa)")


# Schema quản trị người dùng
class UserAdminResponse(BaseModel):
    user_id: int
    email: str
    role: str
    is_active: bool
    created_at: Optional[datetime] = None
    full_name: Optional[str] = None
    company_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }
