"""
Pydantic Schemas cho chức năng Ứng tuyển (Application)
Theo đặc tả SRS UniCareer mục 10.2.5 & 11.2 (Application Module)
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# Schema khi ứng viên nộp hồ sơ ứng tuyển
class ApplicationCreate(BaseModel):
    job_id: int = Field(..., description="ID tin tuyển dụng muốn ứng tuyển")
    candidate_id: Optional[int] = Field(None, description="ID ứng viên (nếu truyền từ client)")
    cover_letter: Optional[str] = Field(None, description="Thư giới thiệu / ghi chú kèm theo")


# Schema khi nhà tuyển dụng cập nhật trạng thái đơn ứng tuyển
class ApplicationStatusUpdate(BaseModel):
    status: str = Field(
        ...,
        description="Trạng thái xử lý đơn: RECEIVED (Đã tiếp nhận), REVIEWING (Đang xem xét), ACCEPTED (Đã chấp nhận), REJECTED (Từ chối)"
    )


# Schema trả về kết quả đơn ứng tuyển cơ bản
class ApplicationResponse(BaseModel):
    application_id: int
    job_id: int
    candidate_id: int
    status: str
    ai_match_score: Optional[int] = None
    ai_feedback: Optional[str] = None
    applied_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }


# Schema chi tiết đơn ứng tuyển đầy đủ thông tin (cho ứng viên hoặc nhà tuyển dụng xem)
class ApplicationDetailResponse(ApplicationResponse):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    company_location: Optional[str] = None
    salary_range: Optional[str] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None
    candidate_university: Optional[str] = None
    candidate_major: Optional[str] = None
    candidate_cv_url: Optional[str] = None
    candidate_skills: Optional[str] = None
