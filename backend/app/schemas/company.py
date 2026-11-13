"""
Pydantic Schemas cho chức năng Doanh nghiệp (Company)
Theo đặc tả SRS UniCareer mục 10.2.3 & Task T85FE99
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Schema chung chứa các trường thông tin cơ bản
class CompanyBase(BaseModel):
    company_name: str = Field(..., min_length=2, max_length=150, description="Tên doanh nghiệp")
    description: Optional[str] = Field(None, description="Mô tả / giới thiệu doanh nghiệp")
    website: Optional[str] = Field(None, max_length=255, description="Website công ty")
    industry: Optional[str] = Field(None, max_length=100, description="Lĩnh vực hoạt động")
    location: Optional[str] = Field(None, max_length=150, description="Địa chỉ trụ sở chính")

# Schema khi tạo mới doanh nghiệp (POST)
class CompanyCreate(CompanyBase):
    employer_id: int = Field(..., description="ID tài khoản nhà tuyển dụng (1-1 với bảng users)")

# Schema khi cập nhật thông tin doanh nghiệp (PUT/PATCH)
class CompanyUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=2, max_length=150, description="Tên doanh nghiệp")
    description: Optional[str] = Field(None, description="Mô tả / giới thiệu doanh nghiệp")
    website: Optional[str] = Field(None, max_length=255, description="Website công ty")
    industry: Optional[str] = Field(None, max_length=100, description="Lĩnh vực hoạt động")
    location: Optional[str] = Field(None, max_length=150, description="Địa chỉ trụ sở chính")

# Schema trả về kết quả (Response)
class CompanyResponse(CompanyBase):
    company_id: int
    employer_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }

# Schema chi tiết kèm thống kê (nếu cần)
class CompanyDetailResponse(CompanyResponse):
    job_count: Optional[int] = 0
