"""
Pydantic Schemas cho chức năng Tin tuyển dụng (Job Post)
Theo đặc tả SRS UniCareer mục 10.2.4 & Task T05FE9A
"""

from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

# Schema chung chứa các trường thông tin cơ bản của tin tuyển dụng
class JobBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, description="Tên vị trí tuyển dụng")
    description: str = Field(..., min_length=5, description="Mô tả công việc chi tiết")
    requirements: str = Field(..., min_length=5, description="Yêu cầu đối với ứng viên")
    location: Optional[str] = Field("TP. Hồ Chí Minh", max_length=100, description="Địa điểm làm việc")
    salary_range: Optional[str] = Field("Thỏa thuận", max_length=100, description="Mức lương / Khoảng lương")
    job_type: Optional[str] = Field("INTERNSHIP", description="Loại hình công việc (FULL_TIME, PART_TIME, INTERNSHIP)")
    experience_level: Optional[str] = Field("Không yêu cầu", max_length=50, description="Kinh nghiệm yêu cầu")
    deadline: Optional[date] = Field(None, description="Hạn cuối nộp hồ sơ")

# Schema khi tạo mới tin tuyển dụng (POST /api/jobs)
class JobCreate(JobBase):
    company_id: Optional[int] = Field(1, description="ID doanh nghiệp đăng tin")
    status: Optional[str] = Field("ACTIVE", description="Trạng thái hiển thị (ACTIVE, CLOSED, HIDDEN)")
    approval_status: Optional[str] = Field("APPROVED", description="Trạng thái duyệt (PENDING, APPROVED, REJECTED)")

# Schema khi cập nhật toàn diện thông tin tin tuyển dụng (PUT /api/jobs/{id})
class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150, description="Tên vị trí tuyển dụng")
    description: Optional[str] = Field(None, min_length=5, description="Mô tả công việc")
    requirements: Optional[str] = Field(None, min_length=5, description="Yêu cầu ứng viên")
    location: Optional[str] = Field(None, max_length=100, description="Địa điểm")
    salary_range: Optional[str] = Field(None, max_length=100, description="Mức lương")
    job_type: Optional[str] = Field(None, description="Loại hình công việc")
    experience_level: Optional[str] = Field(None, max_length=50, description="Kinh nghiệm")
    deadline: Optional[date] = Field(None, description="Hạn nộp hồ sơ")
    status: Optional[str] = Field(None, description="Trạng thái hiển thị (ACTIVE, CLOSED, HIDDEN)")
    approval_status: Optional[str] = Field(None, description="Trạng thái duyệt")

# Schema khi cập nhật nhanh trạng thái đóng/ẩn/mở tin tuyển dụng (PATCH /api/jobs/{id}/status)
class JobStatusUpdate(BaseModel):
    status: str = Field(..., description="Trạng thái mới: ACTIVE (Đang tuyển), CLOSED (Đã đóng), HIDDEN (Tạm ẩn)")

# Schema trả về kết quả tin tuyển dụng (Response)
class JobResponse(JobBase):
    job_id: int
    company_id: int
    status: str
    approval_status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    company_name: Optional[str] = None
    application_count: Optional[int] = 0

    model_config = {
        "from_attributes": True
    }
